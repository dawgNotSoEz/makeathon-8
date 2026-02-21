import { Navigate, Route, Routes, useParams } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { DocumentListPage } from "./pages/DocumentListPage";
import { DocumentViewerPage } from "./pages/DocumentViewerPage";
import { GeneralTemplatePage } from "./pages/GeneralTemplatePage";
import { ProfilePage } from "./pages/ProfilePage";

const DEFAULT_DOCUMENT_ID = "rbi-policy_name";

function LegacyDocumentRedirect() {
  const { documentId } = useParams();
  if (!documentId) {
    return <Navigate to="/documents" replace />;
  }
  return <Navigate to={`/documents/analysis/${documentId}`} replace />;
}

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<GeneralTemplatePage />} />
        <Route path="/documents" element={<DocumentListPage />} />
        <Route path="/documents/analysis" element={<Navigate to={`/documents/analysis/${DEFAULT_DOCUMENT_ID}`} replace />} />
        <Route path="/documents/analysis/:documentId" element={<DocumentViewerPage />} />
        <Route path="/documents/:documentId" element={<LegacyDocumentRedirect />} />
        <Route path="/profile" element={<ProfilePage />} />
      </Routes>
    </AppShell>
  );
}
