const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

try {
    console.log('=== STARTING HYBRID DEPLOYMENT DEPENDENCY INSTALLER ===');
    
    // 1. Detect python command
    let pythonCmd = 'python3';
    try {
        execSync('python3 --version', { stdio: 'ignore' });
    } catch (e) {
        pythonCmd = 'python';
    }
    console.log(`* Detected Python command executable: ${pythonCmd}`);
    
    // 2. Create virtual environment inside project directory
    const venvDir = path.join(__dirname, 'venv');
    if (!fs.existsSync(venvDir)) {
        console.log('* Creating local virtual environment (venv) in project root...');
        execSync(`${pythonCmd} -m venv venv`, { stdio: 'inherit' });
        console.log('  => Virtual environment created successfully.');
    } else {
        console.log('* Virtual environment already exists.');
    }
    
    // 3. Resolve local pip executable
    const pipPath = process.platform === 'win32'
        ? path.join(venvDir, 'Scripts', 'pip.exe')
        : path.join(venvDir, 'bin', 'pip');
        
    if (!fs.existsSync(pipPath)) {
        throw new Error(`Local pip executable not found at: ${pipPath}`);
    }
    
    // 4. Run pip install inside venv
    console.log(`* Installing requirements inside venv using: ${pipPath}...`);
    // On Linux we might need --break-system-packages (though inside venv it's not required, we'll run standard install)
    execSync(`"${pipPath}" install --upgrade pip`, { stdio: 'inherit' });
    execSync(`"${pipPath}" install -r requirements.txt`, { stdio: 'inherit' });
    console.log('  => Python packages installed successfully inside venv.');
    
    console.log('=== HYBRID SETUP COMPLETED SUCCESSFULLY ===');
} catch (err) {
    console.error('  => Failed to set up local virtual environment:', err.message);
    
    // 5. Fallback to system-level pip installation if venv creation fails
    try {
        console.log('* Attempting system-level pip fallback installation...');
        execSync('pip install --break-system-packages -r requirements.txt || pip install -r requirements.txt', { stdio: 'inherit' });
        console.log('  => System-level fallback successful.');
    } catch (fallbackErr) {
        console.error('  => System-level fallback also failed:', fallbackErr.message);
        process.exit(1);
    }
}
