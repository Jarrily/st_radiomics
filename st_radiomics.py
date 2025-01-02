import os
import SimpleITK as sitk
import pandas as pd
import streamlit as st
from io import BytesIO
from radiomics import featureextractor

# 显示数据集目录结构说明
dataset_structure = '''   
/my_dataset  # 数据集目录 
  ├── images/  # 原图数据 （与masks数据命名必须完全一致！！）
  │   ├── XXXXX1.nii.gz
  │   ├── XXXXX2.nii.gz
  │   ├── XXXXX3.nii.gz
  │   ├── XXXXX4.nii.gz
  │   └── ...
  └── masks/  # 掩膜数据 （与images数据命名必须完全一致！！）
      ├── XXXXX1.nii.gz
      ├── XXXXX2.nii.gz
      ├── XXXXX3.nii.gz
      ├── XXXXX4.nii.gz
      └── ...
'''
st.code(dataset_structure, language="python")

# 特征提取的函数
def extract_features(image_folder, mask_folder):
    """提取图像和掩膜的放射学特征"""
    feature_df = pd.DataFrame()  # 初始化一个空的DataFrame存放特征
    images = os.listdir(image_folder)  # 获取图像文件列表
    masks = os.listdir(mask_folder)  # 获取掩膜文件列表
    img_mask_pairs = list(zip(images, masks))  # 将图像和掩膜一一配对

    for img_file, mask_file in img_mask_pairs:
        try:
            # 设置特征提取器的参数
            settings = {
                'binWidth': bin_width,
                'sigma': [sigma_1, sigma_2, sigma_3, sigma_4, sigma_5],
                'Interpolator': sitk.sitkBSpline,
                'resampledPixelSpacing': [resampled_pixel_spacing_1, resampled_pixel_spacing_2,
                                          resampled_pixel_spacing_3],
                'voxelArrayShift': voxel_array_shift,
                'normalize': normalize_flag,
                'normalizeScale': normalize_scale
            }
            extractor = featureextractor.RadiomicsFeatureExtractor(**settings)

            # 根据选择的过滤类型启用特征提取器
            if "All" in selected_types:
                extractor.enableImageTypes(
                    Original={}, Wavelet={}, Square={}, SquareRoot={}, Logarithm={},
                    Exponential={}, Gradient={}, LoG={}, LBP2D={}, LBP3D={}
                )
            else:
                extractor.enableImageTypes(**{type: {} for type in selected_types})

            # 执行特征提取
            image = sitk.ReadImage(os.path.join(image_folder, img_file))
            mask = sitk.ReadImage(os.path.join(mask_folder, mask_file))
            feature_vector = extractor.execute(image, mask)

            # 将特征向量转为DataFrame，并插入文件名
            feature_data = pd.DataFrame.from_dict(feature_vector.values()).T
            feature_data.columns = feature_vector.keys()
            feature_data.insert(0, 'ID_Name', img_file)  # 插入文件名作为第一列
            feature_df = pd.concat([feature_df, feature_data])  # 合并数据

        except Exception as e:
            # 如果出错，显示错误信息，并记录出错文件
            st.error(f"{img_file}: There is a problem with the file, please check or re-mark! ERROR: {str(e)}")
            error_df = pd.DataFrame({'Name': [img_file]})
            feature_df = pd.concat([feature_df, error_df])
            continue

    # 删除一些无用的列
    # feature_df.drop(columns=feature_df.columns[1:38], axis=1, inplace=True)
    # return feature_df


# 输入图像路径和掩膜路径
img_column, mask_column = st.columns(2)
with img_column:
    image_path = st.text_input("Please enter the image path:", key="image_path_input")
with mask_column:
    mask_path = st.text_input("Please enter the mask path:", key="mask_path_input")

# 选择特征提取的类型
selected_types = st.multiselect(
    "Select filter type:",
    ["All", "Original", "Wavelet", "Square", "SquareRoot", "Logarithm",
     "Exponential", "Gradient", "LoG", "LBP2D", "LBP3D"]
)

# 设置特征提取器的参数
sigma_1, sigma_2, sigma_3, sigma_4, sigma_5 = st.columns(5)
with sigma_1:
    sigma_1 = st.number_input("sigma 1：", value=1, key="sigma_1")
with sigma_2:
    sigma_2 = st.number_input("sigma 2：", value=2, key="sigma_2")
with sigma_3:
    sigma_3 = st.number_input("sigma 3：", value=3, key="sigma_3")
with sigma_4:
    sigma_4 = st.number_input("sigma 4：", value=4, key="sigma_4")
with sigma_5:
    sigma_5 = st.number_input("sigma 5：", value=5, key="sigma_5")

# 设置其它参数
bin_width_column, voxel_shift_column, normalize_scale_column = st.columns(3)
with bin_width_column:
    bin_width = st.number_input("binWidth：", value=25.0, key="bin_width")
with voxel_shift_column:
    voxel_array_shift = st.number_input("voxelArrayShift：", value=1000, key="voxel_array_shift")
with normalize_scale_column:
    normalize_scale = st.number_input("normalizeScale：", value=100, key="normalize_scale")

# 设置归一化标志
normalize_flag = st.selectbox("normalize：", ("True", "False"), key="normalize_flag")
normalize_flag = normalize_flag == "True"

# 设置重采样像素间距
resample_column_1, resample_column_2, resample_column_3 = st.columns(3)
with resample_column_1:
    resampled_pixel_spacing_1 = st.number_input("resampledPixelSpacing 1：", value=1.0, key="resample_pixel_spacing_1")
with resample_column_2:
    resampled_pixel_spacing_2 = st.number_input("resampledPixelSpacing 2：", value=1.0, key="resample_pixel_spacing_2")
with resample_column_3:
    resampled_pixel_spacing_3 = st.number_input("resampledPixelSpacing 3：", value=1.0, key="resample_pixel_spacing_3")

# 当点击按钮时，进行特征提取
if st.button('Feature extraction', key="Features_EX"):
    feature_folder = image_path
    mask_folder = mask_path
    features_df = extract_features(feature_folder, mask_folder)

    # 提取成功后，提供下载链接
    st.success("Feature extraction is successful!")
    excel_buffer = BytesIO()
    excel_writer = pd.ExcelWriter(excel_buffer, engine='xlsxwriter')
    features_df.to_excel(excel_writer, sheet_name='Sheet1', index=False)
    excel_writer.close()
    excel_buffer.seek(0)

    st.download_button(
        label="Download the radiomics features",
        data=excel_buffer.read(),
        file_name='Radiomics_Features_all.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# 提供官方文档链接
st.write(
    "For further information, please go to the official website: https://pyradiomics.readthedocs.io/en/latest/features.html")
