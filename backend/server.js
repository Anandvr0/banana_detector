const express = require("express");
const cors = require("cors");
const multer = require("multer");
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

const app = express();
const PORT = 5000;

app.use(cors());

const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, path.join(__dirname, "uploads"));
    },
    filename: (req, file, cb) => {
        const extension = path.extname(file.originalname);
        cb(null, Date.now() + extension);
    }
});

const upload = multer({ storage });

app.use("/output", express.static(path.join(__dirname, "..", "output")));

app.post("/analyze", upload.single("image"), (req, res) => {
    if (!req.file) {
        return res.status(400).json({ error: "No image uploaded" });
    }

    const imagePath = req.file.path;

    const pythonProcess = spawn("python", [
        path.join(__dirname, "..", "curvature.py"),
        imagePath
    ]);

    let output = "";
    let error = "";

    pythonProcess.stdout.on("data", (data) => {
        output += data.toString();
    });

    pythonProcess.stderr.on("data", (data) => {
        error += data.toString();
    });

    pythonProcess.on("close", (code) => {
        fs.unlink(imagePath, () => {});

        if (code !== 0) {
            console.error(error);

            return res.status(500).json({
                error: "Python Analysis Failed",
                details: error
            });
        }

        const confidenceMatch = output.match(/Confidence:\s*([\d.]+)%/);
        const curvatureMatch = output.match(/Curvature score:\s*([\d.]+)\/100/);
        const classificationMatch = output.match(/Classification:\s*(.+)/);
        const verdictMatch = output.match(/Verdict:\s*(.+)/);

        const imageMatch = output.match(/Result saved → (.+)/);

        let imageUrl = null;

        if (imageMatch) {
            const outputPath = imageMatch[1].trim();
            const filename = path.basename(outputPath);
            imageUrl = `http://localhost:${PORT}/output/${filename}`;
        }

        res.json({
            confidence: confidenceMatch ? parseFloat(confidenceMatch[1]) : null,
            curvature: curvatureMatch ? parseFloat(curvatureMatch[1]) : null,
            classification: classificationMatch
                ? classificationMatch[1].trim()
                : null,
            verdict: verdictMatch
                ? verdictMatch[1].trim()
                : null,
            imageUrl: imageUrl
        });
    });
});

app.listen(PORT, () => {
    console.log(`Backend running at http://localhost:${PORT}`);
});