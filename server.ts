import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import { spawn, execSync } from "child_process";

async function startServer() {
  const app = express();
  const PORT = process.env.PORT || 3000;

  // Initialize Telegram Bot if Token is provided (Python process)
  let isBotRunning = false;
  if (process.env.TELEGRAM_BOT_TOKEN) {
    console.log("Installing python requirements...");
    try {
      execSync("python3 -m pip install -r requirements.txt", { stdio: "inherit" });
      console.log("Starting Python bot...");
      const botProc = spawn("python3", ["bot.py"], { stdio: "inherit" });
      isBotRunning = true;
      
      botProc.on("error", (e) => {
        console.error("Bot failed:", e);
        isBotRunning = false;
      });
      botProc.on("exit", () => {
        isBotRunning = false;
      });
    } catch (err) {
      console.error("Failed to start python bot:", err);
    }
  } else {
    console.warn("TELEGRAM_BOT_TOKEN is missing. Bot is not running.");
  }

  // API Backend routes
  app.get("/api/health", (req, res) => {
    res.json({ status: "ok" });
  });

  app.get("/api/stats", (req, res) => {
    res.json({
      botRunning: isBotRunning,
      registeredUsers: "-", // Handled by Python in memory now
      // hardcoding the 30 medical tasks available
      totalQuestions: 30,
      time: new Date().toISOString()
    });
  });

  // Vite Middleware for Frontend Dashboards
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
