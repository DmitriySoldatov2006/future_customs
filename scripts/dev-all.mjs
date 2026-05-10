import fs from 'node:fs';
import path from 'node:path';
import { spawn, spawnSync } from 'node:child_process';

const rootDir = process.cwd();
const appDir = path.join(rootDir, 'app5');
const isWindows = process.platform === 'win32';
const isCheckMode = process.argv.includes('--check');

function exists(targetPath) {
  return fs.existsSync(targetPath);
}

function getPythonBinary(venvDir) {
  return isWindows
    ? path.join(venvDir, 'Scripts', 'python.exe')
    : path.join(venvDir, 'bin', 'python');
}

function getPipArgs(venvDir) {
  return ['-m', 'pip'];
}

function runOrThrow(command, args, options = {}) {
  const result = spawnSync(command, args, {
    stdio: 'inherit',
    cwd: rootDir,
    ...options,
  });

  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

function commandWorks(command, args) {
  const result = spawnSync(command, args, {
    stdio: 'ignore',
    cwd: rootDir,
  });
  return result.status === 0;
}

function resolveSystemPython() {
  const candidates = isWindows
    ? [
        ['py', ['-3', '--version']],
        ['python', ['--version']],
      ]
    : [
        ['python3', ['--version']],
        ['python', ['--version']],
      ];

  for (const [command, args] of candidates) {
    if (commandWorks(command, args)) {
      return command;
    }
  }

  console.error('Python 3 не найден. Установите Python 3 и повторите запуск `npm run dev:all`.');
  process.exit(1);
}

function resolveRequirementsFile() {
  const candidates = [
    path.join(rootDir, 'requirements.txt'),
    path.join(appDir, 'requirements.txt'),
  ];

  return candidates.find(exists) ?? null;
}

function resolveVirtualEnvDir() {
  const preferredDirs = isWindows
    ? [path.join(rootDir, 'venv'), path.join(rootDir, '.venv')]
    : [path.join(rootDir, '.venv'), path.join(rootDir, 'venv')];

  for (const dir of preferredDirs) {
    if (exists(getPythonBinary(dir))) {
      return dir;
    }
  }

  const hasForeignVenv = preferredDirs.some((dir) => exists(dir));
  if (hasForeignVenv) {
    return path.join(rootDir, isWindows ? '.venv-win' : '.venv-macos');
  }

  return preferredDirs[0];
}

function ensureVirtualEnv(venvDir) {
  const pythonBinary = getPythonBinary(venvDir);
  if (exists(pythonBinary)) {
    return pythonBinary;
  }

  fs.mkdirSync(path.dirname(venvDir), { recursive: true });
  const systemPython = resolveSystemPython();
  const createArgs = isWindows ? ['-3', '-m', 'venv', venvDir] : ['-m', 'venv', venvDir];

  console.log(`Создаю виртуальное окружение: ${path.basename(venvDir)}`);
  runOrThrow(systemPython, createArgs);

  return getPythonBinary(venvDir);
}

function ensureDependencies(pythonBinary) {
  const requirementsFile = resolveRequirementsFile();

  if (requirementsFile) {
    console.log(`Устанавливаю зависимости из ${path.relative(rootDir, requirementsFile)}`);
    runOrThrow(pythonBinary, [...getPipArgs(), 'install', '-r', requirementsFile]);
    return;
  }

  if (commandWorks(pythonBinary, ['-c', 'import django'])) {
    return;
  }

  console.log('requirements.txt не найден, устанавливаю Django');
  runOrThrow(pythonBinary, [...getPipArgs(), 'install', 'Django']);
}

function runManagePy(pythonBinary, args) {
  runOrThrow(pythonBinary, ['manage.py', ...args], { cwd: appDir });
}

function startServer(pythonBinary) {
  const child = spawn(pythonBinary, ['manage.py', 'runserver', '8000'], {
    cwd: appDir,
    stdio: 'inherit',
  });

  child.on('exit', (code) => {
    process.exit(code ?? 0);
  });

  for (const signal of ['SIGINT', 'SIGTERM']) {
    process.on(signal, () => {
      child.kill(signal);
    });
  }
}

if (!exists(path.join(appDir, 'manage.py'))) {
  console.error('Не найден файл app5/manage.py. Запустите команду из корня репозитория.');
  process.exit(1);
}

const venvDir = resolveVirtualEnvDir();
const pythonBinary = ensureVirtualEnv(venvDir);

ensureDependencies(pythonBinary);
runManagePy(pythonBinary, ['migrate', '--noinput']);

if (isCheckMode) {
  runManagePy(pythonBinary, ['check']);
  process.exit(0);
}

startServer(pythonBinary);
