import { BrowserRouter, Route, Routes } from "react-router-dom";
import DisclaimerBanner from "./components/DisclaimerBanner";
import HomePage from "./pages/HomePage";
import MatchDetailPage from "./pages/MatchDetailPage";

export default function App() {
  return (
    <BrowserRouter>
      <div className="mx-auto min-h-screen max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
        <DisclaimerBanner />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/match/:id" element={<MatchDetailPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
