import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/common/Navbar';
import Home from './pages/Home';
import Recipes from './pages/Recipes';
import AddRecipe from './pages/AddRecipe';
import RecipeDetail from './pages/RecipeDetail';
import Users from './pages/Users';
import AIChat from './pages/AIChat';
import Login from './components/user/Login';
import Register from './components/user/Register';
import AIWidget from './components/common/AIWidget';
import './styles/globals.css';

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
              <Route path="/recipes" element={<Recipes />} />
              <Route path="/recipes/:id" element={<RecipeDetail />} />
              <Route path="/add-recipe" element={<AddRecipe />} />
              <Route path="/users" element={<Users />} />
              <Route path="/ai-chat" element={<AIChat />} />
            </Routes>
          </main>
          <AIWidget />
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;