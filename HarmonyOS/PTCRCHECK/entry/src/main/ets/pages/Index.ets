import web_webview from '@ohos.web.webview';
import picker from '@ohos.file.picker'; // 引入文件/相册选择器

@Entry
@Component
struct Index {
  controller: web_webview.WebviewController = new web_webview.WebviewController();

  build() {
    Column() {
      Web({
        src: 'https://ptcr-check.xyz',
        controller: this.controller
      })
        .width('100%')
        .height('100%')
        .domStorageAccess(true)
        .javaScriptAccess(true)
        .mixedMode(MixedMode.All)
          // 关键：处理网页上传图片请求
        .onShowFileSelector((event) => {
          this.selectImage(event);
          return true;
        })
    }
    .width('100%')
    .height('100%')
  }

  // 选择图片逻辑
  selectImage(event: any) {
    try {
      let PhotoSelectOptions = new picker.PhotoSelectOptions();
      PhotoSelectOptions.MIMEType = picker.PhotoViewMIMETypes.IMAGE_TYPE; // 仅选择图片
      PhotoSelectOptions.maxSelectNumber = 1; // 选一张

      let photoPicker = new picker.PhotoViewPicker();
      photoPicker.select(PhotoSelectOptions).then((PhotoSelectResult) => {
        if (PhotoSelectResult && PhotoSelectResult.photoUris.length > 0) {
          let filePath = PhotoSelectResult.photoUris[0];
          console.info('Selected file: ' + filePath);

          // 将路径数组传回给网页
          // 在 API 9 中，event.result.handleFileList 是标准方法
          event.result.handleFileList([filePath]);
        } else {
          // 用户取消选择，传空数组防止网页无响应
          event.result.handleFileList([]);
        }
      }).catch((err) => {
        console.error('PhotoPicker failed: ' + JSON.stringify(err));
        event.result.handleFileList([]);
      });
    } catch (err) {
      console.error('Invoke PhotoPicker failed: ' + JSON.stringify(err));
      event.result.handleFileList([]);
    }
  }

  // 物理返回键处理
  onBackPress() {
    if (this.controller.accessBackward()) {
      this.controller.backward();
      return true;
    }
    return false;
  }
}