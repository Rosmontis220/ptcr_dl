import web_webview from '@ohos:web.webview';
import picker from '@ohos:file.picker'; // 引入文件/相册选择器
class Index extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1) {
        super(parent, __localStorage, elmtId);
        this.controller = new web_webview.WebviewController();
        this.setInitiallyProvidedValue(params);
    }
    setInitiallyProvidedValue(params) {
        if (params.controller !== undefined) {
            this.controller = params.controller;
        }
    }
    updateStateVars(params) {
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
    }
    aboutToBeDeleted() {
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    initialRender() {
        this.observeComponentCreation((elmtId, isInitialRender) => {
            ViewStackProcessor.StartGetAccessRecordingFor(elmtId);
            Column.create();
            Column.width('100%');
            Column.height('100%');
            if (!isInitialRender) {
                Column.pop();
            }
            ViewStackProcessor.StopGetAccessRecording();
        });
        this.observeComponentCreation((elmtId, isInitialRender) => {
            ViewStackProcessor.StartGetAccessRecordingFor(elmtId);
            Web.create({
                src: 'https://ptcr-check.xyz',
                controller: this.controller
            });
            Web.width('100%');
            Web.height('100%');
            Web.domStorageAccess(true);
            Web.javaScriptAccess(true);
            Web.mixedMode(MixedMode.All);
            Web.onShowFileSelector((event) => {
                this.selectImage(event);
                return true;
            });
            if (!isInitialRender) {
                Web.pop();
            }
            ViewStackProcessor.StopGetAccessRecording();
        });
        Column.pop();
    }
    // 选择图片逻辑
    selectImage(event) {
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
                }
                else {
                    // 用户取消选择，传空数组防止网页无响应
                    event.result.handleFileList([]);
                }
            }).catch((err) => {
                console.error('PhotoPicker failed: ' + JSON.stringify(err));
                event.result.handleFileList([]);
            });
        }
        catch (err) {
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
    rerender() {
        this.updateDirtyElements();
    }
}
ViewStackProcessor.StartGetAccessRecordingFor(ViewStackProcessor.AllocateNewElmetIdForNextComponent());
loadDocument(new Index(undefined, {}));
ViewStackProcessor.StopGetAccessRecording();
//# sourceMappingURL=Index.js.map