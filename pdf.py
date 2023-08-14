from io import BytesIO
import fitz
from PIL import Image
from tqdm import tqdm

def pdf_compress(_pdf, _dpi=150, _type="png", method=0):
    '''
    本方法适用于纯图片型（包含文字型图片）的PDF文档压缩，可复制型的文字类的PDF文档不建议使用本方法
    :param _pdf: 文件名全路径
    :param _dpi: 转化后图片的像素（范围72-600），默认150，想要清晰点，可以设置成高一点，这个参数直接影响PDF文件大小
                 测试：  纯图片PDF文件（即单个页面就是一个图片，内容不可复制）
                        300dpi，压缩率约为30-50%，即原来大小的30-50%，基本无损，看不出来压缩后导致的分辨率差异
                        200dpi，压缩率约为20-30%，轻微有损
                        150dpi，压缩率约为5-10%，有损，但是基本不影响图片形文字的阅读
    :param _type: 保存格式，默认为png，其他：JPEG, PNM, PGM, PPM, PBM, PAM, PSD, PS
    :param method:  int，图像压缩方法，只支持下面3个选项，默认值是0
                0 : `MEDIANCUT` (median cut)
                1 : `MAXCOVERAGE` (maximum coverage)
                2 : `FASTOCTREE` (fast octree)
    :return:
    '''
    merges = []
    _file = None
    with fitz.open(_pdf) as doc:
        for i, page in tqdm(enumerate(doc.pages(), start=0) , desc="压缩处理中，请耐心等待"):
            img = page.get_pixmap(dpi=_dpi)             # 将PDF页面转化为图片
            img_bytes = img.pil_tobytes(format=_type)   # 将图片转为为bytes对象
            image = Image.open(BytesIO(img_bytes))      # 将bytes对象转为PIL格式的图片对象
            if i == 0:
                _file = image                           # 取第一张图片用于创建PDF文档的首页
            pix: Image.Image = image.quantize(colors=256, method=method).convert('RGB')    # 单张图片压缩处理
            merges.append(pix)                          # 组装pdf
            # tqdm.write(f"\n{i} | success reduced  page: {i}.{_type}")
    

    _file.save(f"{_pdf.rsplit('.')[0]}_by_{_dpi}dpi.pdf",####################路径
               "pdf",                                   # 用PIL自带的功能保存为PDF格式文件
               save_all=True,
               append_images=merges[1:])


    print("All completed！")


if __name__ == '__main__':
    file = 'C:\\Users\\SweetLemon\\Desktop\\aaa.pdf'
    pdf_compress(file, _dpi=72)


