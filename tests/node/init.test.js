// Smoke test for `npx pandex init`: packs the package, installs it into a fresh
// temp project, runs init, and checks the venv + copied files. Needs python3 on PATH.
const { test } = require("node:test");
const assert = require("node:assert/strict");
const { execFileSync, spawnSync } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const repoRoot = path.resolve(__dirname, "..", "..");
const npm = process.platform === "win32" ? "npm.cmd" : "npm";

test("pandex with unknown command prints usage and exits 1", () => {
  const r = spawnSync(process.execPath, [path.join(repoRoot, "bin", "pandex.js"), "bogus"], { encoding: "utf8" });
  assert.equal(r.status, 1);
  assert.match(r.stdout, /Usage: npx pandex init/);
});

test("pandex init sets up venv and copies skill files", { timeout: 10 * 60 * 1000 }, () => {
  const work = fs.mkdtempSync(path.join(os.tmpdir(), "pandex-init-"));
  const tgzName = execFileSync(npm, ["pack", "--pack-destination", work], { cwd: repoRoot, encoding: "utf8" })
    .trim()
    .split("\n")
    .pop();
  const tgz = path.join(work, tgzName);

  // A packed tarball must never contain Python bytecode or dev-only folders.
  const listing = execFileSync("tar", ["-tzf", tgz], { encoding: "utf8" });
  assert.doesNotMatch(listing, /__pycache__|\.pyc|tests\/|test_fixtures|pandex-sandbox/);

  const proj = path.join(work, "proj");
  fs.mkdirSync(proj);
  execFileSync(npm, ["init", "-y"], { cwd: proj, stdio: "ignore" });
  execFileSync(npm, ["install", "--no-audit", "--no-fund", tgz], { cwd: proj, stdio: "ignore" });

  const r = spawnSync(process.execPath, [path.join(proj, "node_modules", "pandexai", "bin", "pandex.js"), "init"], {
    cwd: proj,
    encoding: "utf8",
  });
  assert.equal(r.status, 0, r.stdout + r.stderr);
  assert.match(r.stdout, /PandexAI is ready/);

  for (const f of ["SKILL.md", "commands/clean.md", "commands/gather.md", "scripts/clean.py", "scripts/gather.py", ".claude/commands/pandex.md"]) {
    assert.ok(fs.existsSync(path.join(proj, f)), `missing ${f}`);
  }
  const venvPython =
    process.platform === "win32" ? path.join(proj, ".pandex", "venv", "Scripts", "python.exe") : path.join(proj, ".pandex", "venv", "bin", "python");
  assert.ok(fs.existsSync(venvPython), "venv python missing");

  // The venv must be able to run the real clean script.
  fs.copyFileSync(path.join(repoRoot, "test_fixtures", "messy_data.csv"), path.join(proj, "messy_data.csv"));
  const clean = spawnSync(venvPython, [path.join(proj, "scripts", "clean.py"), "messy_data.csv"], { cwd: proj, encoding: "utf8" });
  assert.equal(clean.status, 0, clean.stderr);
  const report = JSON.parse(clean.stdout);
  assert.equal(report.original_row_count, 6);
  assert.ok(fs.existsSync(path.join(proj, report.cleaned_file)));
});
