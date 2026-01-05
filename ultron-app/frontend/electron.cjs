const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

let mainWindow;
let pythonProcess;

function createWindow() {
  // Determine icon path based on environment
  const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;
  const iconPath = isDev 
    ? path.join(__dirname, 'public', 'icon.jpg')
    : path.join(__dirname, 'dist', 'icon.jpg');

  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    backgroundColor: '#000000',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    },
    frame: true,
    title: 'Ultron AI v5.7',
    icon: iconPath
  });

  // Load the React app
  // In development: http://localhost:3000
  // In production: file://path/to/dist/index.html
  
  if (isDev) {
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools(); // Enable DevTools in development
  } else {
    mainWindow.loadFile(path.join(__dirname, 'dist', 'index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startPythonBackend() {
  let backendCommand;
  let backendArgs = [];
  let backendCwd;
  
  if (app.isPackaged) {
    // Production: Use compiled executable
    backendCommand = path.join(process.resourcesPath, 'backend', 'ultron_engine.exe');
    backendCwd = path.join(process.resourcesPath, 'backend');
    console.log('Starting Python backend (Packaged):', backendCommand);
  } else {
    // Development: Use Python script
    backendCommand = 'python';
    backendArgs = [path.join(__dirname, '..', 'backend', 'server.py')];
    backendCwd = path.join(__dirname, '..', 'backend');
    console.log('Starting Python backend (Development):', backendArgs[0]);
  }
  
  pythonProcess = spawn(backendCommand, backendArgs, {
    cwd: backendCwd,
    stdio: 'pipe'
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log(`[Python Backend] ${data.toString()}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`[Python Backend Error] ${data.toString()}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`Python backend exited with code ${code}`);
  });
}

function stopPythonBackend() {
  if (pythonProcess) {
    console.log('Stopping Python backend...');
    pythonProcess.kill();
    pythonProcess = null;
  }
}

app.on('ready', () => {
  // Start Python backend first
  startPythonBackend();
  
  // Wait 2 seconds for backend to initialize, then open window
  setTimeout(() => {
    createWindow();
  }, 2000);
});

app.on('window-all-closed', () => {
  stopPythonBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

app.on('before-quit', () => {
  stopPythonBackend();
});

// Handle app crashes gracefully
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
  stopPythonBackend();
});
