# ViT_Bamboo_NeurIPS_Code
- [Yuelu Shuyuan Cang Qin Jian (Si--Qi) Wenzi Bian](https://1drv.ms/u/c/4851c5065d666952/EdCTrRsnBtxDm4HwisdhplgBclQzgZF4Un53_WXG0b0EiQ?e=eKQTC5) - Download the PDF resources.

- [Yuelu Shuyuan Cang Qin Jian (Si--Qi) Wenzi Bian](https://1drv.ms/u/c/4851c5065d666952/Ee3G4NuFwYhPpJG7W6gp4dMBzOSqif_FImlpor4MqKae-g?e=qLu1ws) - Data sources for constructing the first stage training dataset and put the downloaded file into ViT_Bamboo_NeurIPS_Code/DATA. Use this dataset:
    ```bash
    unzip DATA/PDFWords.zip
    python notebook/crop_images.py
    ``` 

- [Real Bamboo Slips Datasets](https://1drv.ms/u/c/4851c5065d666952/EUtsyAMIqMlKpONJfRBidNsBMlkPr4eoC_SRixZ4LH9gMQ?e=ZyVVJJ) - Download this dataset and put this dataset into ViT_Bamboo_NeurIPS_Code/DATA. Test the topk results of our model:
    ```bash
    unzip DATA/SDD.zip
    sh test.sh
    ```