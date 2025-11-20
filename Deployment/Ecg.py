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
        """Load image from path or bytes (streamlit saved path)"""
        return imread(image)

    def GrayImgae(self, image):
        image_gray = color.rgb2gray(image)
        image_gray = resize(image_gray, (1572, 2213))
        return image_gray

    def DividingLeads(self, image):
        # Coordinates tuned for your ECG layout
        Lead_1 = image[300:600, 150:643]
        Lead_2 = image[300:600, 646:1135]
        Lead_3 = image[300:600, 1140:1625]
        Lead_4 = image[300:600, 1630:2125]
        Lead_5 = image[600:900, 150:643]
        Lead_6 = image[600:900, 646:1135]
        Lead_7 = image[600:900, 1140:1625]
        Lead_8 = image[600:900, 1630:2125]
        Lead_9 = image[900:1200, 150:643]
        Lead_10 = image[900:1200, 646:1135]
        Lead_11 = image[900:1200, 1140:1625]
        Lead_12 = image[900:1200, 1630:2125]
        Lead_13 = image[1250:1480, 150:2125]

        Leads = [Lead_1, Lead_2, Lead_3, Lead_4, Lead_5,
                 Lead_6, Lead_7, Lead_8, Lead_9, Lead_10,
                 Lead_11, Lead_12, Lead_13]

        # Save preview (12 leads)
        fig, ax = plt.subplots(4, 3)
        fig.set_size_inches(10, 10)
        x, y = 0, 0
        for i, lead in enumerate(Leads[:12]):
            ax[x][y].imshow(lead)
            ax[x][y].axis('off')
            ax[x][y].set_title(f"Leads {i+1}")
            if (i+1) % 3 == 0:
                x += 1
                y = 0
            else:
                y += 1
        leads12_path = self._path("Leads_1-12_figure.png")
        fig.savefig(leads12_path, bbox_inches='tight')
        plt.close(fig)

        # Save long lead preview
        fig2, ax2 = plt.subplots()
        fig2.set_size_inches(10, 4)
        ax2.imshow(Leads[-1])
        ax2.axis('off')
        long_path = self._path("Long_Lead_13_figure.png")
        fig2.savefig(long_path, bbox_inches='tight')
        plt.close(fig2)

        return Leads

    def PreprocessingLeads(self, Leads):
        # preprocess 12 leads and save preview
        fig, ax = plt.subplots(4, 3)
        fig.set_size_inches(10, 10)
        x, y = 0, 0
        for i, lead in enumerate(Leads[:12]):
            gray = color.rgb2gray(lead)
            blur = gaussian(gray, sigma=1)
            thr = threshold_otsu(blur)
            binary = resize(blur < thr, (300, 450))
            ax[x][y].imshow(binary, cmap='gray')
            ax[x][y].axis('off')
            ax[x][y].set_title(f"pre-processed Leads {i+1}")
            if (i+1) % 3 == 0:
                x += 1
                y = 0
            else:
                y += 1
        pre12_path = self._path("Preprocessed_Leads_1-12_figure.png")
        fig.savefig(pre12_path, bbox_inches='tight')
        plt.close(fig)

        # long lead preprocessed
        fig2, ax2 = plt.subplots()
        fig2.set_size_inches(10, 4)
        gray = color.rgb2gray(Leads[-1])
        blur = gaussian(gray, sigma=1)
        thr = threshold_otsu(blur)
        ax2.imshow(blur < thr, cmap='gray')
        ax2.axis('off')
        pre13_path = self._path("Preprocessed_Leads_13_figure.png")
        fig2.savefig(pre13_path, bbox_inches='tight')
        plt.close(fig2)

    def SignalExtraction_Scaling(self, Leads):
        # delete previous Scaled CSVs inside base_dir to avoid accumulation
        for f in os.listdir(self.base_dir):
            if f.startswith("Scaled_1DLead_") and f.endswith(".csv"):
                try:
                    os.remove(self._path(f))
                except Exception:
                    pass

        fig, ax = plt.subplots(4, 3)
        fig.set_size_inches(10, 10)
        x, y = 0, 0

        for i, lead in enumerate(Leads[:12]):
            gray = color.rgb2gray(lead)
            blur = gaussian(gray, sigma=0.7)
            thr = threshold_otsu(blur)
            binary = resize(blur < thr, (300, 450))
            conts = measure.find_contours(binary, 0.8)
            if not conts:
                # skip if no contours found for this lead
                continue

            # choose the largest contour by length and resize to (255,2)
            cont = sorted(conts, key=lambda c: c.shape[0], reverse=True)[0]
            cont = resize(cont, (255, 2))

            ax[x][y].invert_yaxis()
            ax[x][y].plot(cont[:, 1], cont[:, 0], linewidth=1)
            ax[x][y].axis('off')
            ax[x][y].set_title(f"Contour {i+1}")
            if (i+1) % 3 == 0:
                x += 1
                y = 0
            else:
                y += 1

            # scale and save
            scaler = MinMaxScaler()
            scaled = scaler.fit_transform(cont)
            df = pd.DataFrame(scaled[:, 0]).T
            csv_name = f"Scaled_1DLead_{i+1}.csv"
            df.to_csv(self._path(csv_name), index=False)

        contour_path = self._path("Contour_Leads_1-12_figure.png")
        fig.savefig(contour_path, bbox_inches='tight')
        plt.close(fig)

    def CombineConvert1Dsignal(self):
        files = [f for f in natsorted(os.listdir(self.base_dir))
                 if f.startswith("Scaled_1DLead_") and f.endswith(".csv")]
        if not files:
            raise FileNotFoundError("No Scaled_1DLead_*.csv files found. SignalExtraction_Scaling may have failed.")
        dfs = [pd.read_csv(self._path(f)) for f in files]
        final_df = pd.concat(dfs, axis=1, ignore_index=True)
        return final_df

    def DimensionalReduciton(self, test_final):
        pca_path = self._path("PCA_ECG.pkl")
        if not os.path.isfile(pca_path):
            raise FileNotFoundError(f"PCA model missing at {pca_path}")
        pca = joblib.load(pca_path)
        result = pca.transform(test_final)
        return pd.DataFrame(result)

    def ModelLoad_predict(self, final_df):
        model_path = self._path("Heart_Disease_Prediction_using_ECG.pkl")
        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"Classifier model missing at {model_path}")
        model = joblib.load(model_path)
        result = model.predict(final_df)
        return (
            "You ECG corresponds to Myocardial Infarction" if result[0] == 1 else
            "You ECG corresponds to Abnormal Heartbeat" if result[0] == 0 else
            "Your ECG is Normal" if result[0] == 2 else
            "You ECG corresponds to History of Myocardial Infarction"
        )
