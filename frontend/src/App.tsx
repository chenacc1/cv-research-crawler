import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppShell from './components/layout/AppShell';
import DashboardPage from './pages/DashboardPage';
import PaperListPage from './pages/PaperListPage';
import PaperDetailPage from './pages/PaperDetailPage';
import RepoListPage from './pages/RepoListPage';
import RepoDetailPage from './pages/RepoDetailPage';
import TagManagePage from './pages/TagManagePage';
import ReportListPage from './pages/ReportListPage';
import ReportViewPage from './pages/ReportViewPage';
import CrawlStatusPage from './pages/CrawlStatusPage';
import KeywordManagePage from './pages/KeywordManagePage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/papers" element={<PaperListPage />} />
          <Route path="/papers/:id" element={<PaperDetailPage />} />
          <Route path="/repos" element={<RepoListPage />} />
          <Route path="/repos/:id" element={<RepoDetailPage />} />
          <Route path="/tags" element={<TagManagePage />} />
          <Route path="/reports" element={<ReportListPage />} />
          <Route path="/reports/:id" element={<ReportViewPage />} />
          <Route path="/crawls" element={<CrawlStatusPage />} />
          <Route path="/keywords" element={<KeywordManagePage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
