# Ecg.py
import os
from skimage.io import imread
from skimage import color, measure
from skimage.filters import threshold_otsu, gaussian
from skimage.transform import resize
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
import joblib
from natsort import natsorted

class ECG:
    def __init__(self):
        # base directory where this file lives (Deployment/)
        self.base_dir = os.path.dirname(__file__)

    def _path(self, filename):
        """Return absolute path inside the deployment folder"""
        return os.path.join(self.base_dir, filename)

    def getImage(self, image):
        """
        this functions gets user image
        return: user image (numpy array)
        """
        # image may be a path string
        image = imread(image)
        return image

    def GrayImgae(self, image):
        """
        This function converts the user image to Gray Scale
        return: Gray scale Image
        """
        image_gray = color.rgb2gray(image)
        image_gray = resize(image_gray, (1572, 2213))
        return image_gray

    def DividingLeads(self, image):
        """
        Divide ECG image into 13 leads (12 + long lead)
        returns: list of 13 lead images and also saves two preview PNGs
        """
        Lead_1 = image[300:600, 150:643]      # Lead 1
        Lead_2 = image[300:600, 646:1135]     # Lead aVR
        Lead_3 = image[300:600, 1140:1625]    # Lead V1
        Lead_4 = image[300:600, 1630:2125]    # Lead V4
        Lead_5 = image[600:900, 150:643]      # Lead 2
        Lead_6 = image[600:900, 646:1135]     # Lead aVL
        Lead_7 = image[600:900, 1140:1625]    # Lead V2
        Lead_8 = image[600:900, 1630:2125]    # Lead V5
        Lead_9 = image[900:1200, 150:643]     # Lead 3
        Lead_10 = image[900:1200, 646:1135]   # Lead aVF
        Lead_11 = image[900:1200, 1140:1625]  # Lead V3
        Lead_12 = image[900:1200, 1630:2125]  # Lead V6
        Lead_13 = image[1250:1480, 150:2125]  # Long Lead

        Leads = [Lead_1, Lead_2, Lead_3, Lead_4, Lead_5, Lead_6, Lead_7, Lead_8, Lead_9, Lead_10, Lead_11, Lead_12, Lead_13]

        # create 12-lead preview
        try:
            fig, ax = plt.subplots(4, 3)
            fig.set_size_inches(10, 10)
            x_counter = 0
            y_counter = 0
            for x, y in enumerate(Leads[:12]):
                ax[x_counter][y_counter].imshow(y)
                ax[x_counter][y_counter].axis('off')
                ax[x_counter][y_counter].set_title(f"Leads {x+1}")
                if (x+1) % 3 == 0:
                    x_counter += 1
                    y_counter = 0
                else:
                    y_counter += 1

            leads12_path = self._path('Leads_1-12_figure.png')
            fig.savefig(leads12_path)
            plt.close(fig)
        except Exception:
            try:
                plt.close('all')
            except Exception:
                pass

        # long lead preview
        try:
            fig1, ax1 = plt.subplots()
            fig1.set_size_inches(10, 10)
            ax1.imshow(Lead_13)
            ax1.set_title("Leads 13")
            ax1.axis('off')
            longlead_path = self._path('Long_Lead_13_figure.png')
            fig1.savefig(longlead_path)
            plt.close(fig1)
        except Exception:
            try:
                plt.close('all')
            except Exception:
                pass

        return Leads

    def PreprocessingLeads(self, Leads):
        """
        Preprocess each extracted lead and save preview images
        """
        try:
            fig2, ax2 = plt.subplots(4, 3)
            fig2.set_size_inches(10, 10)
            x_counter = 0
            y_counter = 0

            for x, y in enumerate(Leads[:12]):
                grayscale = color.rgb2gray(y)
                blurred_image = gaussian(grayscale, sigma=1)
                global_thresh = threshold_otsu(blurred_image)
                binary_global = blurred_image < global_thresh
                binary_global = resize(binary_global, (300, 450))

                ax2[x_counter][y_counter].imshow(binary_global, cmap="gray")
                ax2[x_counter][y_counter].axis('off')
                ax2[x_counter][y_counter].set_title(f"pre-processed Leads {x+1} image")
                if (x+1) % 3 == 0:
                    x_counter += 1
                    y_counter = 0
                else:
                    y_counter += 1

            pre12_path = self._path('Preprossed_Leads_1-12_figure.png')
            fig2.savefig(pre12_path)
            plt.close(fig2)
        except Exception:
            try:
                plt.close('all')
            except Exception:
                pass

        # lead 13
        try:
            fig3, ax3 = plt.subplots()
            fig3.set_size_inches(10, 10)
            grayscale = color.rgb2gray(Leads[-1])
            blurred_image = gaussian(grayscale, sigma=1)
            global_thresh = threshold_otsu(blurred_image)
            binary_global = blurred_image < global_thresh
            ax3.imshow(binary_global, cmap='gray')
            ax3.set_title("Leads 13")
            ax3.axis('off')
            pre13_path = self._path('Preprossed_Leads_13_figure.png')
            fig3.savefig(pre13_path)
            plt.close(fig3)
        except Exception:
            try:
                plt.close('all')
            except Exception:
                pass

    def SignalExtraction_Scaling(self, Leads):
        """
        Extract contours from each lead and save scaled 1D CSVs in the deployment folder.
        """
        # DELETE previous CSVs (fix infinite looping)
        try:
            for f in os.listdir(self.base_dir):
                if f.startswith("Scaled_1DLead_") and f.endswith(".csv"):
                    try:
                        os.remove(self._path(f))
                    except Exception:
                        pass
        except Exception:
            pass

        try:
            fig4, ax4 = plt.subplots(4, 3)
            x_counter = 0
            y_counter = 0

            for x, y in enumerate(Leads[:12]):
                grayscale = color.rgb2gray(y)
                blurred_image = gaussian(grayscale, sigma=0.7)
                global_thresh = threshold_otsu(blurred_image)
                binary_global = blurred_image < global_thresh
                binary_global = resize(binary_global, (300, 450))
                contours = measure.find_contours(binary_global, 0.8)
                if not contours:
                    # if no contour found, skip saving and continue
                    continue

                # pick the biggest contour by length
                contour = sorted(contours, key=lambda c: c.shape[0], reverse=True)[0]
                contour_resized = resize(contour, (255, 2))

                ax4[x_counter][y_counter].invert_yaxis()
                ax4[x_counter][y_counter].plot(contour_resized[:, 1], contour_resized[:, 0], linewidth=1)
                ax4[x_counter][y_counter].axis('image')
                ax4[x_counter][y_counter].set_title(f"Contour {x+1} image")
                if (x+1) % 3 == 0:
                    x_counter += 1
                    y_counter = 0
                else:
                    y_counter += 1

                # scaling and saving as CSV (one row)
                scaler = MinMaxScaler()
                fit_transform_data = scaler.fit_transform(contour_resized)
                Normalized_Scaled = pd.DataFrame(fit_transform_data[:, 0], columns=['X']).T
                csv_filename = f"Scaled_1DLead_{x+1}.csv"
                csv_path = self._path(csv_filename)
                Normalized_Scaled.to_csv(csv_path, index=False)

            contour_fig_path = self._path('Contour_Leads_1-12_figure.png')
            fig4.savefig(contour_fig_path)
            plt.close(fig4)
        except Exception:
            try:
                plt.close('all')
            except Exception:
                pass

    def CombineConvert1Dsignal(self):
        """
        Combines all Scaled_1DLead_*.csv into a single DataFrame in the same order (1..12).
        returns the final dataframe
        """
        files = [f for f in natsorted(os.listdir(self.base_dir)) if f.startswith('Scaled_1DLead_') and f.endswith('.csv')]
        if not files:
            raise FileNotFoundError("No Scaled_1DLead_*.csv files found. SignalExtraction_Scaling may have failed.")

        dfs = [pd.read_csv(self._path(f)) for f in files]
        test_final = pd.concat(dfs, axis=1, ignore_index=True)
        return test_final

    def DimensionalReduciton(self, test_final):
        """
        Use saved PCA model to reduce dims
        """
        model_filename = 'PCA_ECG.pkl'
        model_path = self._path(model_filename)

        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"PCA model not found at: {model_path}. Please add PCA_ECG.pkl to the deployment folder.")

        pca_loaded_model = joblib.load(model_path)
        result = pca_loaded_model.transform(test_final)
        final_df = pd.DataFrame(result)
        return final_df

    def ModelLoad_predict(self, final_df):
        """
        Load pretrained classifier and predict
        """
        model_filename = 'Heart_Disease_Prediction_using_ECG.pkl'
        model_path = self._path(model_filename)

        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"Classifier model not found at: {model_path}. Please add Heart_Disease_Prediction_using_ECG.pkl to the deployment folder.")

        model = joblib.load(model_path)
        result = model.predict(final_df)
        if result[0] == 1:
            return "You ECG corresponds to Myocardial Infarction"
        elif result[0] == 0:
            return "You ECG corresponds to Abnormal Heartbeat"
        elif result[0] == 2:
            return "Your ECG is Normal"
        else:
            return "You ECG corresponds to History of Myocardial Infarction"
