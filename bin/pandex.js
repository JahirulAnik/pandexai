#!/usr/bin/env node
const { execSync, spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const args = process.argv.slice(2);
const command = args[0];

if (command !== "init") {
  console.log("Usage: npx pandex init");
  process.exit(1);
}

const cwd = process.cwd();
const venvDir = path.join(cwd, ".pandex", "venv");

function findPython() {
  for (const name of ["python3", "python"]) {
    const result = spawnSync(name, ["--version"], { stdio: "ignore" });
    if (result.status === 0) return name;
  }
  return null;
}

console.log("Setting up PandexAI...");

const pythonCmd = findPython();
if (!pythonCmd) {
  console.error("ERROR: No Python installation found on your PATH.");
  console.error("PandexAI needs Python 3 to run its data profiling scripts.");
  console.error("Install Python from https://python.org and try again.");
  process.exit(1);
}
console.log(`Found Python: ${pythonCmd}`);

if (!fs.existsSync(venvDir)) {
  console.log("Creating virtual environment at .pandex/venv ...");
  const venvResult = spawnSync(pythonCmd, ["-m", "venv", venvDir], { stdio: "inherit" });
  if (venvResult.status !== 0) {
    console.error("ERROR: Failed to create virtual environment.");
    process.exit(1);
  }
} else {
  console.log(".pandex/venv already exists, skipping creation.");
}

const isWindows = process.platform === "win32";
const venvPython = isWindows
  ? path.join(venvDir, "Scripts", "python.exe")
  : path.join(venvDir, "bin", "python");

console.log("Installing pandas into the virtual environment...");
const installResult = spawnSync(venvPython, ["-m", "pip", "install", "--quiet", "pandas"], { stdio: "inherit" });
if (installResult.status !== 0) {
  console.error("ERROR: Failed to install pandas.");
  process.exit(1);
}

const packageRoot = path.join(__dirname, "..");
const filesToCopy = ["SKILL.md", "commands", "scripts"];

function copyRecursive(src, dest) {
  const stat = fs.statSync(src);
  if (stat.isDirectory()) {
    if (!fs.existsSync(dest)) fs.mkdirSync(dest, { recursive: true });
    for (const entry of fs.readdirSync(src)) {
      copyRecursive(path.join(src, entry), path.join(dest, entry));
    }
  } else {
    fs.copyFileSync(src, dest);
  }
}

console.log("Copying PandexAI files into your project...");
for (const item of filesToCopy) {
  const src = path.join(packageRoot, item);
  const dest = path.join(cwd, item);
  if (fs.existsSync(src)) {
    copyRecursive(src, dest);
  }
}

console.log("");
console.log("PandexAI is ready. Try: /pandex scan <your-file.csv> inside your AI CLI.");
