import LoginPage from './components/LoginPage';
import OperatorDashboard from './pages/OperatorDashboard';
import OutboxReview from './pages/OutboxReview';
import CallAnalyticsPage from './pages/CallAnalyticsPage';
import CommunicationHistoryPage from './pages/CommunicationHistoryPage';
import SettingsPage from './pages/SettingsPage';
import PrivateRoute from './components/PrivateRoute';
import MainLayout from './components/MainLayout';
import { Routes, Route } from 'react-router-dom';

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<PrivateRoute />}>
        <Route element={<MainLayout />}>
          <Route path="/" element={<OperatorDashboard />} />
          <Route path="/outbox" element={<OutboxReview />} />
          <Route path="/call-analytics" element={<CallAnalyticsPage />} />
          <Route path="/communication-history" element={<CommunicationHistoryPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Route>
    </Routes>
  );
}

export default App;
