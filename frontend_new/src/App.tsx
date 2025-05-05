import LoginPage from './components/LoginPage';
import OperatorDashboard from './pages/OperatorDashboard';
import OutboxReview from './pages/OutboxReview';
import PrivateRoute from './components/PrivateRoute';
import { Routes, Route } from 'react-router-dom';

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<PrivateRoute />}>
        <Route path="/" element={<OperatorDashboard />} />
        <Route path="/outbox" element={<OutboxReview />} />
      </Route>
    </Routes>
  );
}

export default App;
