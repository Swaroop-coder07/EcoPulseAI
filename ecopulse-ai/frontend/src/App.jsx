
import { Navigate, Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import NotificationBell from "./components/NotificationBell.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Buildings from "./pages/Buildings.jsx";
import Analytics from "./pages/Analytics.jsx";
import Actions from "./pages/Actions.jsx";

export default function App() {
  return (
    <div className="min-h-screen">
      <Navbar />

      <div className="mx-auto flex max-w-6xl justify-end px-4 pt-4">
        <NotificationBell />
      </div>

      <main className="mx-auto max-w-6xl px-4 py-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/buildings" element={<Buildings />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/actions" element={<Actions />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
