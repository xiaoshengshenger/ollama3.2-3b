import { useAppStore } from '../stores/appStore';
import { storeToRefs } from 'pinia';
import { type CodeValidateResult } from '../types/index';
export default function (){
    const appStore = useAppStore();
    const { apiUrl } = storeToRefs(appStore);

    
    async function validateCode(code:string=appStore.code): Promise<CodeValidateResult> {
        try {
            const requestBody = {
                code: "PGPT-TvzqMtT0yt9P-RTd59+IWzndI-Utr4y1biCVpt-VYDxUFxBNoKn-jA66px+715Fd-HgQEYkKDyP4l-9DjJqoSfz26F-8vQ9WWGA5xXf-cCnwpWbXZ+8Y-RTNULwBdlcWb-v08Sh/x6EUtO-QKl4J1wpp1xm-DDPIayJIP7Up-zPzTGyCTBRFG-eQPG3tNXzYii-PekXFGXndXYj-++zJ8IQrARoe-OwG3AxV5Ib1x-y6r54/ONT0GM-xHM8tuGXMDI/-qBkPI3rlBVG9-t/72XFtfYidI-c2hhjOuclNkC-upxoCBveiFka-W5oy95JCwQfu-mPqmfvxaPtfc-cy4LZH67CEIt-bY0UxolR6chd-grKOtI4mioIN-gtjrmSuJZQRY-O7fqWuDGFod0-fYg9aMkZyuNv-8XWrY98JlDic-MxqP3OmB2GMX-/wer1jHUJrpW-j5jzVDmvg394-339p5fWMfXgz-kfO1Gt01WnD/-4UVnby2k0XOV-cIq6MihHRruJ-SHXv/3cbnjce-Px3eTOdtzsUB-PquoPxcJhI+Q-iqSCXcYcnBck-qAy/Mg=="
            };
            const response = await fetch(`${apiUrl.value}meta/code`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
          });
          console.error("验证激活码请求：", response.ok,"==============", response.body);
          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `API 响应错误: ${response.status} ${response.statusText}`);
          }

          const result: CodeValidateResult = await response.json();
          console.log("激活码验证成功，返回数据：", result);
          return result;
        } catch (error) {
            const errMsg = error instanceof Error ? error.message : "未知错误";
            console.error("验证激活码请求出错：", errMsg);
            // 可在这里添加用户提示（比如弹窗）
            // ElMessage.error(`激活码验证失败：${errMsg}`); // 如果用 Element Plus 等组件库
            throw error; // 抛出错误，让调用方也能捕获
        }
        
    }
    return {validateCode}
}