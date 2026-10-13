import { spawn } from "node:child_process";

const command = process.execPath;
const children = [
  spawn(command, ["node_modules/tsx/dist/cli.mjs", "server/index.ts"], { stdio: "inherit" }),
  spawn(command, ["node_modules/vite/bin/vite.js"], { stdio: "inherit" }),
];

const stop = () => {
  for (const child of children) child.kill();
};

process.on("SIGINT", stop);
process.on("SIGTERM", stop);
for (const child of children) child.on("exit", (code) => {
  if (code && code !== 0) process.exitCode = code;
});
