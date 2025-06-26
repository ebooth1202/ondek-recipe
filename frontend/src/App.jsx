import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/common/Navbar';
import Home from './pages/Home';
import Login from './components/user/Login';
import Register from './components/user/Register';
import Dashboard from './pages/Dashboard';
import Recipes from './pages/Recipes';
import AddRecipe from './pages/AddRecipe';
import RecipeDetail from './pages/RecipeDetail';
import Users from './pages/Users';
import UserManagement from './components/user/UserManagement';
import AIChat from './pages/AIChat';
import AdminIssues from './pages/AdminIssues'; // ADD THIS LINE

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Navbar />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/recipes" element={<Recipes />} />
              <Route path="/add-recipe" element={<AddRecipe />} />
              <Route path="/recipes/:id" element={<RecipeDetail />} />
              <Route path="/users" element={<Users />} />
              <Route path="/user-management" element={<UserManagement />} />
              <Route path="/ai-chat" element={<AIChat />} />
              <Route path="/admin/issues" element={<AdminIssues />} /> {/* ADD THIS LINE */}
            </Routes>
          </main>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;