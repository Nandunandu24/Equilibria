const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// POST endpoint to evaluate operational pricing and inventory safety policies
app.post('/api/evaluate', (req, res) => {
    // Resolve python command dynamically, preferring local virtual environment if it exists
    let pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
    
    const venvPath = process.platform === 'win32'
        ? path.join(__dirname, 'venv', 'Scripts', 'python.exe')
        : path.join(__dirname, 'venv', 'bin', 'python');
        
    if (fs.existsSync(venvPath)) {
        pythonCmd = venvPath;
    }
    
    const pythonProcess = spawn(pythonCmd, [path.join(__dirname, 'api_bridge.py')]);
    
    let stdoutData = '';
    let stderrData = '';
    
    // Write request parameters to python process standard input as JSON
    pythonProcess.stdin.write(JSON.stringify(req.body));
    pythonProcess.stdin.end();
    
    // Read stdout from python process
    pythonProcess.stdout.on('data', (data) => {
        stdoutData += data.toString();
    });
    
    // Read stderr from python process (for debugging and logging errors)
    pythonProcess.stderr.on('data', (data) => {
        stderrData += data.toString();
    });
    
    // Handle process completion
    pythonProcess.on('close', (code) => {
        if (code !== 0) {
            console.error(`Python script exited with code ${code}. Error: ${stderrData}`);
            return res.status(500).json({ error: 'Analytical engine error', details: stderrData });
        }
        
        try {
            const results = JSON.parse(stdoutData.trim());
            res.json(results);
        } catch (e) {
            console.error(`Failed to parse Python JSON output: ${stdoutData}. Error: ${e.message}`);
            res.status(500).json({ error: 'Failed to parse engine output', details: stdoutData });
        }
    });
});

app.listen(PORT, () => {
    console.log(`Command Center running at http://localhost:${PORT}`);
});
