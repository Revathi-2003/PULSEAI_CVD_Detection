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
        """Read an image from a path-like (streamlit saved file)"""
        return imread(image)

    def GrayImgae(self, image):
        """Convert to grayscale and resize to canonical size"""
        image_gray = color.rgb2gray(image)
        image_gray = resize(image_gray, (1572, 2213))
        return image_gray

    def DividingLeads(self, image):
        """Crop the full ECG into 13 lead images and save a preview figure"""
        # cropping coordinates (tuned to your input format)
        Lead_1 = image[300:600, 150:643]      # Lead 1
        Lead_2 = image[300:600, 646:1135]     # Lead 2
        Lead_3 = image[300:600, 1140:1625]    # Lead 3
        Lead_4 = image[300:600, 1630:2125]    # Lead 4
        Lead_5 = image[600:900, 150:643]      # Lead 5
        Lead_6 = image[600:900, 646:1135]     # Lead 6
        Lead_7 = image[600:900, 1140:1625]    # Lead 7
        Lead_8 = image[600:900, 1630:2125]    # Lead 8
        Lead_9 = image[900:1200, 150:643]     # Lead 9
        Lead_10 = image[900:1200, 646:1135]   # Lead 10
        Lead_11 = image[900:1200, 1140:1625]  # Lead 11
        Lead_12 = image[900:1200, 1630:2125]  # Lead 12
        Lead_13 = image[1250:1480, 150:2125]  # Long Lead

        Leads = [Lead_1, Lead_2, Lead_3, Lead_4, Lead_5, Lead_6, Lead_7, Lead_8, Lead_9, Lead_10, Lead_11, Lead_12, Lead_13]

        # 12-lead preview figure
        try:
            fig, ax = plt.subplots(4, 3)
            fig.set_size_inches(10, 10)
            x_counter = 0
            y_counter = 0
            for idx, lead in enumerate(Leads[:12]):
                ax[x_counter][y_counter].imshow(lead)
                ax[x_counter][y_counter].axis('off')
                ax[x_counter][y_counter].set_title(f"Leads {idx+1}")
                if (idx+1) % 3 == 0:
                    x_counter += 1
                    y_counter = 0
                else:
                    y_counter += 1
            fig.savefig(self._path('Leads_1-12_figure.png'))
            plt.close(fig)
        except Exception:
            # keep going if preview generation fails
            try:
                plt.close('all')
            except Exception:
                pass

        # long lead preview
        try:
            fig1, ax1 = plt.subplots()
            fig1.set_size_inches(10, 10)
            ax1.imshow(Lead_13)
            ax1.axis('off')
            fig1.savefig(self._path('Long_Lead_13_figure.png'))
            plt.close(fig1)
        except Exception:
            try:
                plt.close('all')
            except Exception:
                pass

        return Leads

    def PreprocessingLeads(self, Leads):
        """Preprocess each of the 12 leads for contour extraction and save previews"""
        try:
            fig2, ax2 = plt.subplots(4, 3)
            fig2.set_size_inches(10, 10)
            x_counter = 0
            y_counter = 0
            for idx, lead in enumerate(Leads[:12]):
                grayscale = color.rgb2gray(lead)
                blurred_image = gaussian(grayscale, sigma=1)
                global_thresh = threshold_otsu(blurred_image)
                binary_global = blurred_image < global_thresh
                binary_global = resize(binary_global, (300, 450))

                ax2[x_counter][y_counter].imshow(binary_global, cmap="gray")
                ax2[x_counter][y_counter].axis('off')
                ax2[x_counter][y_counter].set_title(f"pre-processed Leads {idx+1} image")
                if (idx+1) % 3 == 0:
                    x_counter += 1
                    y_counter = 0
                else:
                    y_counter += 1

            fig2.savefig(self._path('Preprossed_Leads_1-12_figure.png'))
            plt.close(fig2)
        except Exception:
            try:
                plt.close('all')
            except Exception:
                pass

        # long lead preprocessed preview
        try:
            fig3, ax3 = plt.subplots()
            fig3.set_size_inches(10, 10)
            grayscale = color.rgb2gray(Leads[-1])
            blurred_image = gaussian(grayscale, sigma=1)
            global_thresh = threshold_otsu(blurred_image)
            binary_global = blurred_image < global_thresh
            ax3.imshow(binary_global, cmap='gray')
            ax3.axis('off')
            fig3.savefig(self._path('Preprossed_Leads_13_figure.png'))
            plt.close(fig3)
        except Exception:
            try:
                plt.close('all')
            except Exception:
                pass

    def SignalExtraction_Scaling(self, Leads):
        """Find contours on each lead, scale to [0,1], and save as Scaled_1DLead_X.csv"""
        # remove previous CSVs to avoid accumulation or collisions
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
            for idx, lead in enumerate(Leads[:12]):
                grayscale = color.rgb2gray(lead)
                blurred_image = gaussian(grayscale, sigma=0.7)
                global_thresh = threshold_otsu(blurred_image)
                binary_global = blurred_image < global_thresh
                binary_global = resize(binary_global, (300, 450))
                contours = measure.find_contours(binary_global, 0.8)
                if not contours:
                    # skip this lead if no contour found
                    continue

                # choose the longest contour
                contour = sorted(contours, key=lambda c: c.shape[0], reverse=True)[0]
                contour = resize(contour, (255, 2))

                ax4[x_counter][y_counter].invert_yaxis()
                ax4[x_counter][y_counter].plot(contour[:, 1], contour[:, 0], linewidth=1)
                ax4[x_counter][y_counter].axis('image')
                ax4[x_counter][y_counter].set_title(f"Contour {idx+1} image")
                if (idx+1) % 3 == 0:
                    x_counter += 1
                    y_counter = 0
                else:
                    y_counter += 1

                # scale and save as single-row CSV (one lead per column when combined)
                scaler = MinMaxScaler()
                scaled = scaler.fit_transform(contour)
                df = pd.DataFrame(scaled[:, 0]).T
                csv_filename = f"Scaled_1DLead_{idx+1}.csv"
                df.to_csv(self._path(csv_filename), index=False)
            fig4.savefig(self._path('Contour_Leads_1-12_figure.png'))
            plt.close(fig4)
        except Exception:
            try:
                plt.close('all')
            except Exception:
                pass

    def CombineConvert1Dsignal(self):
        """Combine Scaled_1DLead_*.csv files into a single dataframe (ordered by lead index)"""
        files = [f for f in natsorted(os.listdir(self.base_dir)) if f.startswith("Scaled_1DLead_") and f.endswith(".csv")]
        if not files:
            raise FileNotFoundError("No Scaled_1DLead_*.csv files found. Signal extraction may have failed.")
        dfs = []
        for f in files:
            dfs.append(pd.read_csv(self._path(f)))
        final_df = pd.concat(dfs, axis=1, ignore_index=True)
        return final_df

    def DimensionalReduciton(self, test_final):
        """Load PCA model and transform features"""
        model_path = self._path("PCA_ECG.pkl")
        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"PCA model not found at: {model_path}")
        pca = joblib.load(model_path)
        result = pca.transform(test_final)
        return pd.DataFrame(result)

    def ModelLoad_predict(self, final_df):
        """Load classifier and predict"""
        model_path = self._path("Heart_Disease_Prediction_using_ECG.pkl")
        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"Classifier model not found at: {model_path}")
        model = joblib.load(model_path)
        result = model.predict(final_df)
        # map numeric to messages (keep same mapping as before)
        if result[0] == 1:
            return "You ECG corresponds to Myocardial Infarction"
        elif result[0] == 0:
            return "You ECG corresponds to Abnormal Heartbeat"
        elif result[0] == 2:
            return "Your ECG is Normal"
        else:
            return "You ECG corresponds to History of Myocardial Infarction"
