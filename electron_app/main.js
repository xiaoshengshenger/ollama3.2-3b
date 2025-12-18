// 1. 补充缺失的 path 模块（关键！preload 路径需要）
const { app, BrowserWindow } = require('electron');
const path = require('path'); // 新增：引入路径模块
const fs = require('fs'); 

// 解决 Electron 20+ 版本的安全警告
process.env.ELECTRON_DISABLE_SECURITY_WARNINGS = 'true';

const isDev = process.env.NODE_ENV === 'development';

app.disableHardwareAcceleration();
// 声明窗口变量，避免被垃圾回收
let mainWindow;

function watchFrontendChanges() {
  const frontendDir = path.resolve(__dirname, './'); // 请根据实际文件位置修改！

  try {
    // 递归监听前端目录下的所有文件（HTML/CSS/JS 等）
    fs.watch(frontendDir, { recursive: true }, (eventType, filename) => {
      // 过滤临时文件（避免无效刷新，如 .swp、.DS_Store、编译缓存等）
      const ignoreFiles = [
        '.swp', '.DS_Store', '.tmp', '.log', 
        'node_modules', 'dist', 'build', '.vscode', '.idea'
      ];
      if (ignoreFiles.some(suffix => filename?.includes(suffix))) return;

      // 打印变化日志（方便调试）
      console.log(`✅ 前端文件更新：${filename}，自动刷新页面...`);

      // 确保窗口已创建且未关闭，才执行刷新
      if (mainWindow && mainWindow.webContents && !mainWindow.isDestroyed()) {
        mainWindow.webContents.reload(); // 自动刷新页面
      }
    });
    console.log(`📌 已启动前端文件监听，目录：${frontendDir}`);
  } catch (error) {
    console.error('❌ 监听前端文件失败：', error.message);
  }
}

// 统一的创建窗口函数（只保留一处配置，避免冲突）
function createWindow() {
  // 销毁已存在的窗口（防止多开）
  if (mainWindow) {
    mainWindow.close();
  }

  // 核心配置：关闭 Node 集成 + 开启上下文隔离（解决 FormData 问题）
  mainWindow = new BrowserWindow({
    width: 2000,
    height: 700,
    webPreferences: {
      nodeIntegration: true, // 必须关闭（核心）
      contextIsolation: false, // 必须开启（核心）
      webSecurity: false, // 允许跨域请求后端
      allowRunningInsecureContent: true, // 允许加载本地资源
      preload: path.join(__dirname, 'preload.js'), // preload 路径（即使没创建 preload.js 也不会报错）
      nodeIntegrationInWorker: true
    }
  });
  mainWindow.webContents.openDevTools();
  console.log(isDev,"~~~~~~~~~~~~",path.join(__dirname, './dist/index.html'));

  if (isDev) {
    mainWindow.loadURL('http://127.0.0.1:5173');
    // 自动打开开发者工具
    mainWindow.webContents.openDevTools();
  } else {
    // 生产环境：加载 Vite 构建后的 dist/index.html（关键：适配你的 outDir: 'dist'）
    mainWindow.loadFile(path.join(__dirname, './dist/index.html'));
    
  }

  watchFrontendChanges();

  // 窗口关闭时清空变量
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}


// 应用就绪后创建窗口
app.whenReady().then(createWindow);

// 适配 Windows/Linux：关闭所有窗口后退出
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// 适配 macOS：点击 Dock 图标重新创建窗口
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
    // 新增：macOS 重新创建窗口后，重新启动文件监听
    watchFrontendChanges();
  }
});