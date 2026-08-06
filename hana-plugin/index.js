import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";
import fs from "node:fs";

export default class OCGoWidgetPlugin {
  async onload() {
    const { log } = this.ctx;
    const __dirname = path.dirname(fileURLToPath(import.meta.url));
    const widgetDir = path.resolve(__dirname, "..");
    const script = path.join(widgetDir, "main.py");

    if (!fs.existsSync(script)) {
      log.warn(`oc-go-widget: main.py not found at ${script}`);
      return;
    }

    const python = process.env.OC_GO_WIDGET_PYTHON ?? "python";
    const proc = spawn(python, [script], {
      cwd: widgetDir,
      stdio: "ignore",
      windowsHide: true,
    });

    proc.on("error", (err) => {
      log.error(`oc-go-widget spawn error: ${err.message}`);
    });
    proc.on("exit", (code) => {
      log.info(`oc-go-widget exited code=${code}`);
    });

    this.register(() => {
      try {
        proc.kill();
      } catch {
        /* 已退出则忽略 */
      }
      // Windows 兜底：杀掉整个进程树（含 WebView2 子进程）
      if (process.platform === "win32" && proc.pid) {
        spawn("taskkill", ["/PID", String(proc.pid), "/T", "/F"], {
          stdio: "ignore",
          windowsHide: true,
        });
      }
    });

    log.info(`oc-go-widget launched pid=${proc.pid}`);
  }
}
