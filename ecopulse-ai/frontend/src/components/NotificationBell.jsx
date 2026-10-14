
import { useCallback, useEffect, useState } from "react";

const API_BASE = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");
const READ_KEY = "ecopulse-notifications-read";
const SEEN_KEY = "ecopulse-browser-notifications-seen";

async function getItems(path) {
  const response = await fetch(`${API_BASE}/api/${path}`);

  if (!response.ok) {
    throw new Error(`Could not load ${path}`);
  }

  const data = await response.json();
  if (Array.isArray(data)) return data;
  if (Array.isArray(data.items)) return data.items;
  if (Array.isArray(data.alerts)) return data.alerts;
  if (Array.isArray(data.recommendations)) return data.recommendations;
  return [];
}

function buildNotifications(alerts, recommendations) {
  const critical = alerts
    .filter((a) =>
      ["critical", "high"].includes(
        String(a.severity || "").toLowerCase()
      )
    )
    .map((a) => ({
      id: `alert-${a.id}`,
      type: "alert",
      title: `${a.severity || "High"} ${a.resource_type || "resource"} alert`,
      message: `${a.building_name || a.building?.name || "Campus"}: ${
        a.hypothesis || "Unusual resource consumption detected."
      }`,
      timestamp: a.created_at || a.timestamp,
      priority: "high",
    }));

  const pending = recommendations
    .filter((a) => String(a.status || "pending").toLowerCase() === "pending")
    .map((a) => ({
      id: `action-${a.id}`,
      type: "action",
      title: "Action pending",
      message: a.description || "A recommended sustainability action needs attention.",
      timestamp: a.created_at || null,
      priority: "normal",
    }));

  return [...critical, ...pending].sort(
    (a, b) =>
      new Date(b.timestamp || 0).getTime() -
      new Date(a.timestamp || 0).getTime()
  );
}

function readSet(key) {
  try {
    return new Set(JSON.parse(localStorage.getItem(key) || "[]"));
  } catch {
    return new Set();
  }
}
const testBrowserNotification = () => {
  if (!("Notification" in window)) {
    alert("Browser notifications supported nahi hain");
    return;
  }

  if (Notification.permission === "granted") {
    new Notification("EcoPulse AI 🚨", {
      body: "Test successful! Browser notifications kaam kar rahi hain.",
    });
  } else {
    alert("Notification permission: " + Notification.permission);
  }
};
export default function NotificationBell() {
  const [items, setItems] = useState([]);
  const [readIds, setReadIds] = useState(() => readSet(READ_KEY));
  const [open, setOpen] = useState(false);
  const [error, setError] = useState("");
  const [permission, setPermission] = useState(
    "Notification" in window ? Notification.permission : "unsupported"
  );

  const refresh = useCallback(async (isInitial = false) => {
    try {
      const [alerts, recommendations] = await Promise.all([
        getItems("alerts"),
        getItems("recommendations"),
      ]);

      const next = buildNotifications(alerts, recommendations);
      setItems(next);
      setError("");

      // Notify only for new alerts after the initial load.
      const currentIds = new Set(next.map((item) => item.id));
      const knownIds = readSet(SEEN_KEY);

      if (isInitial && !localStorage.getItem(SEEN_KEY)) {
        localStorage.setItem(SEEN_KEY, JSON.stringify([...currentIds]));
      } else if (permission === "granted") {
        next
          .filter((item) => !knownIds.has(item.id) && item.priority === "high")
          .forEach((item) => {
            new Notification(item.title, {
              body: item.message,
              tag: item.id,
            });
          });

        localStorage.setItem(
          SEEN_KEY,
          JSON.stringify([...new Set([...knownIds, ...currentIds])])
        );
      }
    } catch (err) {
      setError("Notifications load nahi hui. Backend check karein.");
      console.error(err);
    }
  }, [permission]);

  useEffect(() => {
    refresh(true);

    const timer = window.setInterval(() => refresh(false), 60_000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  function markRead(id) {
    const next = new Set(readIds);
    next.add(id);
    setReadIds(next);
    localStorage.setItem(READ_KEY, JSON.stringify([...next]));
  }

  function markAllRead() {
    const next = new Set([...readIds, ...items.map((item) => item.id)]);
    setReadIds(next);
    localStorage.setItem(READ_KEY, JSON.stringify([...next]));
  }

  async function enableBrowserNotifications() {
    if (!("Notification" in window)) {
      setPermission("unsupported");
      return;
    }

    const result = await Notification.requestPermission();
    setPermission(result);
    if (result === "granted") refresh(false);
  }

  const unread = items.filter((item) => !readIds.has(item.id)).length;

  return (
    <div className="relative">
      
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-label={`Notifications, ${unread} unread`}
        aria-expanded={open}
        className="relative rounded-lg border border-slate-200 p-2 hover:bg-slate-50"
      >
        <span aria-hidden="true">🔔</span>
        {unread > 0 && (
          <span className="absolute -right-1 -top-1 rounded-full bg-red-600 px-1.5 text-xs text-white">
            {unread > 99 ? "99+" : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 max-w-[90vw] rounded-xl border border-slate-200 bg-white p-3 text-slate-900 shadow-xl">
          <div className="mb-3 flex items-center justify-between gap-2">
            <h2 className="font-semibold">Notifications</h2>
            <button
              type="button"
              onClick={markAllRead}
              className="text-xs text-emerald-700 hover:underline"
            >
              Mark all read
            </button>
          </div>

          {permission !== "granted" && permission !== "unsupported" && (
            <button
              type="button"
              onClick={enableBrowserNotifications}
              className="mb-3 w-full rounded-lg bg-emerald-50 p-2 text-sm text-emerald-800"
            >
              Enable browser notifications
            </button>
          )}

          {permission === "unsupported" && (
            <p className="mb-2 text-xs text-slate-500">
              Is browser mein notifications supported nahi hain.
            </p>
          )}

          {error && (
            <p role="alert" className="mb-2 text-sm text-red-600">
              {error}
            </p>
          )}

          {items.length === 0 && !error && (
            <p className="py-5 text-center text-sm text-slate-500">
              No notifications right now.
            </p>
          )}

          <div className="max-h-96 space-y-2 overflow-y-auto">
            {items.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => markRead(item.id)}
                className={`block w-full rounded-lg border p-3 text-left ${
                  readIds.has(item.id)
                    ? "border-slate-100 bg-white"
                    : "border-emerald-100 bg-emerald-50"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="text-sm font-semibold">{item.title}</span>
                  {!readIds.has(item.id) && (
                    <span className="text-xs text-emerald-700">New</span>
                  )}
                </div>
                <p className="mt-1 text-sm text-slate-600">{item.message}</p>
                {item.timestamp && (
                  <p className="mt-1 text-xs text-slate-400">
                    {new Date(item.timestamp).toLocaleString()}
                  </p>
                )}
              </button>
            ))}
          </div>

          <button
            type="button"
            onClick={() => refresh(false)}
            className="mt-3 w-full rounded-lg border p-2 text-sm hover:bg-slate-50"
          >
            Refresh
          </button>
        </div>
      )}
    </div>
  );
}
