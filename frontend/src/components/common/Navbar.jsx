import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const Navbar = () => {
  const { user, logout, isAuthenticated, hasRole } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const isActive = (path) => {
    return location.pathname === path;
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-brand">
          🍳 onDEK Recipe
        </Link>

        <ul className="navbar-nav">
          {isAuthenticated() ? (
            <>
              <li>
                <Link
                  to="/recipes"
                  className={`nav-link ${isActive('/recipes') ? 'active' : ''}`}
                >
                  Search Recipes
                </Link>
              </li>
              <li>
                <Link
                  to="/add-recipe"
                  className={`nav-link ${isActive('/add-recipe') ? 'active' : ''}`}
                >
                  Add Recipe
                </Link>
              </li>
              {hasRole(['admin', 'owner']) && (
                <li>
                  <Link
                    to="/users"
                    className={`nav-link ${isActive('/users') ? 'active' : ''}`}
                  >
                    Users
                  </Link>
                </li>
              )}
              <li>
                <Link
                  to="/ai-chat"
                  className={`nav-link ${isActive('/ai-chat') ? 'active' : ''}`}
                >
                  AI Chat
                </Link>
              </li>
              <li>
                <span className="nav-link" style={{ color: '#ccc' }}>
                  Welcome, {user?.username}!
                </span>
              </li>
              <li>
                <button
                  onClick={handleLogout}
                  className="btn btn-secondary btn-small"
                >
                  Logout
                </button>
              </li>
            </>
          ) : (
            <>
              <li>
                <Link
                  to="/login"
                  className={`nav-link ${isActive('/login') ? 'active' : ''}`}
                >
                  Login
                </Link>
              </li>
              <li>
                <Link
                  to="/register"
                  className={`nav-link ${isActive('/register') ? 'active' : ''}`}
                >
                  Register
                </Link>
              </li>
            </>
          )}
        </ul>
      </div>
    </nav>
  );
};

export default Navbar;