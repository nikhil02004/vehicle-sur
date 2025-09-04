import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import UploadVideo from './components/UploadVideo';
import Analytics from './components/Analytics';
import BlacklistManager from './components/BlacklistManager';
import Settings from './components/Settings';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<UploadVideo />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="blacklist" element={<BlacklistManager />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </div>
    </Router>
  );
}

export default App;
