import cv2
import json
import argparse
import numpy as np

# THIS CODE IS USING TO GENERATE THE XML FILE FROM THE JSON FILE

# Definición de variables globales
DEFAULT_JSON = '../config_files/stereoParameters.json'
DEFAULT_XML = '../config_files/newStereoMap.xml'
IMG_LEFT = '../images/originals/IMG_LEFT.jpg'
IMG_RIGHT = '../images/originals/IMG_RIGHT.jpg'

def stereo_rectify(params):
    return cv2.stereoRectify(
        params['cameraMatrix1'], params['distCoeffs1'], params['cameraMatrix2'], params['distCoeffs2'], params['imageSize'],
        params['stereoR'], params['stereoT'], flags=cv2.CALIB_ZERO_DISPARITY, alpha=0)

def create_rectify_map(cameraMatrix, distCoeffs, rectification, projection, imageSize):
    return cv2.initUndistortRectifyMap(cameraMatrix, distCoeffs, rectification,
                                       projection, imageSize, cv2.CV_16SC2)

def save_stereo_maps(file_name, stereo_maps, Q):
    cv_file = cv2.FileStorage(file_name, cv2.FILE_STORAGE_WRITE)
    cv_file.write('stereoMapL_x', stereo_maps['Left'][0])
    cv_file.write('stereoMapL_y', stereo_maps['Left'][1])
    cv_file.write('stereoMapR_x', stereo_maps['Right'][0])
    cv_file.write('stereoMapR_y', stereo_maps['Right'][1])
    cv_file.write('disparity2depth_matrix', Q)
    cv_file.release()

def remap_image(image, map_x, map_y):
    return cv2.remap(image, map_x, map_y, cv2.INTER_LANCZOS4, cv2.BORDER_CONSTANT, 0)

def draw_lines(image, gap, imageSize):
    for i in range(1, int(imageSize[1]/gap)+1):
        y = gap * i
        cv2.line(image, (0, y), (imageSize[0], y), (0, 255, 0), 1)
    return image

def visualize_images(window_name, images, size):
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, size[0], size[1])
    cv2.imshow(window_name, images)




def parse_args():
    parser = argparse.ArgumentParser(description='Stereo image processing and rectification.')
    parser.add_argument('--json', default=DEFAULT_JSON, help='JSON file with stereo calibration parameters.')
    parser.add_argument('--xml', default=DEFAULT_XML, help='Output XML file for stereo rectification maps.')
    parser.add_argument('--img_left', help='Left image file name.')
    parser.add_argument('--img_right', help='Right image file name.')
    return parser.parse_args()


def load_stereo_parameters(path):
    with open(path, 'r') as file:
        params = json.load(file)
        params['cameraMatrix1'] = np.transpose(np.array(params['cameraMatrix1']))
        params['cameraMatrix2'] = np.transpose(np.array(params['cameraMatrix2']))
        params['distCoeffs1'] = np.array(params['distCoeffs1'])
        params['distCoeffs2'] = np.array(params['distCoeffs2'])
        params['imageSize'] = tuple([params['imageSize'][1], params['imageSize'][0]])
        params['stereoR'] = np.transpose(np.array(params['stereoR']))
        params['stereoT'] = np.array(params['stereoT'])
    return params


def main():
    args = parse_args()

    parameters = load_stereo_parameters(args.json)
    rectification = stereo_rectify(parameters)
    stereo_maps = {
        'Left': create_rectify_map(parameters['cameraMatrix1'], parameters['distCoeffs1'], rectification[0], rectification[2], parameters['imageSize']),
        'Right': create_rectify_map(parameters['cameraMatrix2'], parameters['distCoeffs2'], rectification[1], rectification[3], parameters['imageSize'])
    }
    save_stereo_maps(args.xml, stereo_maps, rectification[4])
    
    if (args.img_left or args.img_right):

        img_left = cv2.imread(args.img_left)
        img_right = cv2.imread(args.img_right)
        img_left = remap_image(img_left, stereo_maps['Left'][0], stereo_maps['Left'][1])
        img_right = remap_image(img_right, stereo_maps['Right'][0], stereo_maps['Right'][1])

        img_left = draw_lines(img_left, 27, parameters['imageSize'])
        img_right = draw_lines(img_right, 27, parameters['imageSize'])

        vis = np.concatenate((img_left, img_right), axis=1)
        visualize_images('Combined View', vis, (1920, 540))
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    print("Done...")

if __name__ == '__main__':
    main()