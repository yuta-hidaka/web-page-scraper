import os
import traceback
import cv2
import numpy as np
from skimage.metrics import structural_similarity

def pad_image(image, target_shape):
    """Pad the image to match the target shape."""
    target_height, target_width = target_shape[:2]
    height, width = image.shape[:2]

    pad_y = (target_height - height) // 2
    pad_x = (target_width - width) // 2

    padded_image = cv2.copyMakeBorder(image, pad_y, pad_y, pad_x, pad_x, cv2.BORDER_CONSTANT, value=[0, 0, 0])
    return padded_image

def align_images(image1, image2):
    """Align image2 to image1 using ORB feature detection and homography."""
    orb = cv2.ORB_create()

    keypoints1, descriptors1 = orb.detectAndCompute(image1, None)
    keypoints2, descriptors2 = orb.detectAndCompute(image2, None)

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = matcher.match(descriptors1, descriptors2)

    matches = sorted(matches, key=lambda x: x.distance)
    good_matches = matches[:10]

    points1 = np.zeros((len(good_matches), 2), dtype=np.float32)
    points2 = np.zeros((len(good_matches), 2), dtype=np.float32)

    for i, match in enumerate(good_matches):
        points1[i, :] = keypoints1[match.queryIdx].pt
        points2[i, :] = keypoints2[match.trainIdx].pt

    h, mask = cv2.findHomography(points2, points1, cv2.RANSAC)
    height, width = image1.shape[:2]
    aligned_image = cv2.warpPerspective(image2, h, (width, height))

    return aligned_image

def make_diff_image(before_img_path, after_img_path, save_dir):
    print("make_diff_image request start")
    try:
        # Load images
        before = cv2.imread(before_img_path)
        after = cv2.imread(after_img_path)

        if before is None or after is None:
            print("Error: One of the images could not be loaded.")
            return

        # Save original images
        cv2.imwrite(os.path.join(save_dir, 'before.jpg'), before)
        cv2.imwrite(os.path.join(save_dir, 'after.jpg'), after)

        # Convert images to grayscale
        before_gray = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
        after_gray = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)

        # Align after image to before image
        after_aligned = align_images(before_gray, after_gray)

        # Pad the images to the same dimensions
        max_height = max(before_gray.shape[0], after_aligned.shape[0])
        max_width = max(before_gray.shape[1], after_aligned.shape[1])
        target_shape = (max_height, max_width)

        before_padded = pad_image(before, target_shape)
        after_padded = pad_image(cv2.cvtColor(after_aligned, cv2.COLOR_GRAY2BGR), target_shape)

        # Save padded images
        cv2.imwrite(os.path.join(save_dir, 'before_padded.jpg'), before_padded)
        cv2.imwrite(os.path.join(save_dir, 'after_padded.jpg'), after_padded)

        # Convert images to grayscale again after padding
        before_gray_padded = cv2.cvtColor(before_padded, cv2.COLOR_BGR2GRAY)
        after_gray_padded = cv2.cvtColor(after_padded, cv2.COLOR_BGR2GRAY)

        # Compute SSIM between the two images
        (score, diff) = structural_similarity(before_gray_padded, after_gray_padded, full=True)
        print("Image Similarity: {:.4f}%".format(score * 100))

        # The diff image contains the actual image differences between the two images
        # and is represented as a floating point data type in the range [0,1] 
        # so we must convert the array to 8-bit unsigned integers in the range
        # [0,255] before we can use it with OpenCV
        diff = (diff * 255).astype("uint8")
        diff_box = cv2.merge([diff, diff, diff])

        # Save diff images
        cv2.imwrite(os.path.join(save_dir, 'diff.jpg'), diff)
        cv2.imwrite(os.path.join(save_dir, 'diff_box.jpg'), diff_box)

        # Threshold the difference image, followed by finding contours to
        # obtain the regions of the two input images that differ
        thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        contours = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = contours[0] if len(contours) == 2 else contours[1]

        mask = np.zeros(before_padded.shape, dtype='uint8')
        filled_after = after_padded.copy()

        for c in contours:
            area = cv2.contourArea(c)
            if area > 40:
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(before_padded, (x, y), (x + w, y + h), (36, 255, 12), 2)
                cv2.rectangle(after_padded, (x, y), (x + w, y + h), (36, 255, 12), 2)
                cv2.rectangle(diff_box, (x, y), (x + w, y + h), (36, 255, 12), 2)
                cv2.drawContours(mask, [c], 0, (255, 255, 255), -1)
                cv2.drawContours(filled_after, [c], 0, (0, 255, 0), -1)

        # Save mask image
        cv2.imwrite(os.path.join(save_dir, 'mask.jpg'), mask)

        # Combine before and after images side by side
        combined = np.hstack((before_padded, after_padded))
        
        # Ensure the save directory exists
        os.makedirs(save_dir, exist_ok=True)
        
        # Save the resulting combined image
        save_path = os.path.join(save_dir, 'combined.jpg')
        cv2.imwrite(save_path, combined)
        print(f"Output saved to {save_path}")

    except Exception as e:
        print("An error occurred:")
        print(traceback.format_exc())

# Example usage:
# make_diff_image('before.jpg', 'after.jpg', 'output_directory')
