import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Fraction } from 'fraction.js';

const AddRecipe = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  // Form state
  const [formData, setFormData] = useState({
    recipe_name: '',
    serving_size: 1,
    genre: 'dinner'
  });

  const [ingredients, setIngredients] = useState([
    { name: '', quantity: '', unit: 'cup' }
  ]);

  const [instructions, setInstructions] = useState(['']);

  // Options state
  const [availableUnits, setAvailableUnits] = useState([
    'cup', 'cups', 'tablespoon', 'tablespoons', 'teaspoon', 'teaspoons',
    'ounce', 'ounces', 'pound', 'pounds', 'gram', 'grams',
    'kilogram', 'kilograms', 'liter', 'liters', 'milliliter', 'milliliters',
    'piece', 'pieces', 'whole', 'pinch', 'dash'
  ]);

  const [availableGenres, setAvailableGenres] = useState([
    'breakfast', 'lunch', 'dinner', 'snack', 'dessert', 'appetizer'
  ]);

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Authentication check
  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/login');
    }
  }, [isAuthenticated, navigate]);

  // Fetch options from API
  useEffect(() => {
    const fetchOptions = async () => {
      try {
        const [unitsRes, genresRes] = await Promise.all([
          axios.get('http://127.0.0.1:8000/measuring-units'),
          axios.get('http://127.0.0.1:8000/genres')
        ]);
        setAvailableUnits(unitsRes.data.units);
        setAvailableGenres(genresRes.data.genres);
      } catch (error) {
        console.error('Error fetching options:', error);
        // Keep default values if API fails
      }
    };

    if (isAuthenticated()) {
      fetchOptions();
    }
  }, [isAuthenticated]);

  // Fraction utilities
  const parseQuantity = (value) => {
    if (value === undefined || value === null || value === '') return '';

    try {
      // If it's already a number, return it
      if (typeof value === 'number') return value;

      // Convert to string to ensure we can use string methods
      const stringValue = String(value);

      // Handle simple numeric values
      if (!stringValue.includes('/')) {
        return parseFloat(stringValue);
      }

      // Handle mixed numbers (e.g., "1 1/2")
      if (stringValue.includes(' ')) {
        const [whole, fractionPart] = stringValue.split(' ');
        const [numerator, denominator] = fractionPart.split('/');

        return parseFloat(whole) + (parseFloat(numerator) / parseFloat(denominator));
      }

      // Handle simple fractions (e.g., "1/2")
      const [numerator, denominator] = stringValue.split('/');
      return parseFloat(numerator) / parseFloat(denominator);
    } catch (e) {
      console.error("Error parsing fraction:", e);
      return '';
    }
  };

  const formatQuantity = (value) => {
    if (value === undefined || value === null || value === '') return '';

    try {
      // Handle integer values
      if (Number.isInteger(Number(value))) {
        return String(value);
      }

      // Convert to fraction
      const frac = new Fraction(value);

      // If it's a proper fraction (less than 1)
      if (frac.compare(1) < 0) {
        return `${frac.n}/${frac.d}`;
      }

      // If it's an improper fraction (greater than or equal to 1)
      const wholePart = Math.floor(frac.valueOf());
      const fractionalPart = frac.subtract(wholePart);

      if (fractionalPart.valueOf() === 0) {
        return String(wholePart);
      }

      return `${wholePart} ${fractionalPart.n}/${fractionalPart.d}`;
    } catch (e) {
      console.error("Error formatting fraction:", e);
      return String(value);
    }
  };

  const validateQuantity = (value) => {
    if (value === undefined || value === null || value === '') return true;

    // If value is a number, it's valid
    if (typeof value === 'number') return true;

    // Convert to string to ensure we can use string methods
    const stringValue = String(value);

    // Check for valid numeric input
    if (!stringValue.includes('/')) {
      return !isNaN(stringValue);
    }

    try {
      // Check for valid mixed number
      if (stringValue.includes(' ')) {
        const [whole, fractionPart] = stringValue.split(' ');
        if (isNaN(whole)) return false;

        const [numerator, denominator] = fractionPart.split('/');
        return !isNaN(numerator) && !isNaN(denominator) && parseInt(denominator) !== 0;
      }

      // Check for valid simple fraction
      const [numerator, denominator] = stringValue.split('/');
      return !isNaN(numerator) && !isNaN(denominator) && parseInt(denominator) !== 0;
    } catch (e) {
      return false;
    }
  };

  // Form handlers
  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  // Ingredient handlers
  const handleIngredientChange = (index, field, value) => {
    const newIngredients = [...ingredients];

    if (field === 'quantity') {
      // For quantity field, validate the input
      if (validateQuantity(value)) {
        // Parse the fraction to a float for storage
        if (value) {
          try {
            const parsedValue = parseQuantity(value);
            newIngredients[index][field] = parsedValue;
          } catch (e) {
            console.error("Invalid fraction:", e);
            // Keep the string value for display but mark as invalid
            newIngredients[index][field] = value;
          }
        } else {
          newIngredients[index][field] = '';
        }
      } else {
        // For invalid input, keep the string but don't convert
        newIngredients[index][field] = value;
      }
    } else {
      // For other fields, just update normally
      newIngredients[index][field] = value;
    }

    setIngredients(newIngredients);
  };

  const addIngredient = () => {
    setIngredients([...ingredients, { name: '', quantity: '', unit: 'cup' }]);
  };

  const removeIngredient = (index) => {
    if (ingredients.length > 1) {
      const newIngredients = ingredients.filter((_, i) => i !== index);
      setIngredients(newIngredients);
    }
  };

  const handleIngredientKeyDown = (index, field, e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      // If this is the last ingredient and it has content, add a new one
      if (index === ingredients.length - 1 && ingredients[index].name.trim()) {
        addIngredient();
        // Focus the next ingredient name field after a short delay
        setTimeout(() => {
          const nextInput = document.querySelector(`input[data-ingredient-index="${index + 1}"][data-field="name"]`);
          if (nextInput) nextInput.focus();
        }, 100);
      } else if (index < ingredients.length - 1) {
        // Move to next ingredient
        const nextInput = document.querySelector(`input[data-ingredient-index="${index + 1}"][data-field="name"]`);
        if (nextInput) nextInput.focus();
      }
    }
  };

  const handleIngredientBlur = (index, field) => {
    // Format quantities as fractions on blur
    if (field === 'quantity') {
      const value = ingredients[index].quantity;
      if (value && validateQuantity(value)) {
        const newIngredients = [...ingredients];
        if (typeof value === 'string' && (value.includes('/') || !isNaN(value))) {
          newIngredients[index].quantity = parseQuantity(value);
        } else {
          // If it's already a number, no need to parse
          newIngredients[index].quantity = value;
        }
        setIngredients(newIngredients);
      }
    }

    // Auto-add new ingredient row if this is the last one and has content
    if (index === ingredients.length - 1 &&
        ingredients[index].name.trim() &&
        ingredients[index].quantity !== '') {
      setTimeout(() => addIngredient(), 100);
    }
  };

  // Instruction handlers
  const handleInstructionChange = (index, value) => {
    const newInstructions = [...instructions];
    newInstructions[index] = value;
    setInstructions(newInstructions);
  };

  const addInstruction = () => {
    setInstructions([...instructions, '']);
  };

  const removeInstruction = (index) => {
    if (instructions.length > 1) {
      const newInstructions = instructions.filter((_, i) => i !== index);
      setInstructions(newInstructions);
    }
  };

  const handleInstructionKeyDown = (index, e) => {
    if (e.key === 'Enter' && e.shiftKey === false) {
      e.preventDefault();
      // If this is the last instruction and it has content, add a new one
      if (index === instructions.length - 1 && instructions[index].trim()) {
        addInstruction();
        // Focus the next instruction field after a short delay
        setTimeout(() => {
          const nextTextarea = document.querySelector(`textarea[data-instruction-index="${index + 1}"]`);
          if (nextTextarea) nextTextarea.focus();
        }, 100);
      } else if (index < instructions.length - 1) {
        // Move to next instruction
        const nextTextarea = document.querySelector(`textarea[data-instruction-index="${index + 1}"]`);
        if (nextTextarea) nextTextarea.focus();
      }
    }
  };

  const handleInstructionBlur = (index) => {
    // Auto-add new instruction row if this is the last one and has content
    if (index === instructions.length - 1 && instructions[index].trim()) {
      setTimeout(() => addInstruction(), 100);
    }
  };

  // Form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    // Validate form
    if (!formData.recipe_name.trim()) {
      setError('Recipe name is required');
      setLoading(false);
      return;
    }

    const validIngredients = ingredients.filter(ing =>
      ing.name.trim() && ing.quantity !== '' && ing.quantity !== null && ing.quantity !== undefined
    );

    if (validIngredients.length === 0) {
      setError('At least one valid ingredient is required');
      setLoading(false);
      return;
    }

    const validInstructions = instructions.filter(inst => inst.trim());

    if (validInstructions.length === 0) {
      setError('At least one instruction is required');
      setLoading(false);
      return;
    }

    try {
      const recipeData = {
        recipe_name: formData.recipe_name.trim(),
        serving_size: parseInt(formData.serving_size),
        genre: formData.genre,
        ingredients: validIngredients.map(ing => ({
          name: ing.name.trim(),
          quantity: parseFloat(ing.quantity),
          unit: ing.unit
        })),
        instructions: validInstructions.map(inst => inst.trim())
      };

      console.log('Submitting recipe:', recipeData);
      const response = await axios.post('http://127.0.0.1:8000/recipes', recipeData);

      console.log('Recipe created:', response.data);
      setSuccess('Recipe created successfully! 🎉');

      // Reset form
      setFormData({ recipe_name: '', serving_size: 1, genre: 'dinner' });
      setIngredients([{ name: '', quantity: '', unit: 'cup' }]);
      setInstructions(['']);

      // Redirect after a short delay
      setTimeout(() => {
        navigate('/recipes');
      }, 2000);

    } catch (error) {
      console.error('Error creating recipe:', error);
      setError(error.response?.data?.detail || 'Failed to create recipe');
    }

    setLoading(false);
  };

  // Styles
  const containerStyle = {
    padding: '2rem',
    backgroundColor: '#f0f8ff',
    minHeight: 'calc(100vh - 80px)'
  };

  const formContainerStyle = {
    maxWidth: '800px',
    margin: '0 auto',
    background: 'white',
    border: '2px solid #003366',
    borderRadius: '15px',
    padding: '2rem',
    boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)'
  };

  const titleStyle = {
    textAlign: 'center',
    color: '#003366',
    fontSize: '2.5rem',
    marginBottom: '2rem'
  };

  const labelStyle = {
    display: 'block',
    marginBottom: '0.5rem',
    color: '#003366',
    fontWeight: '500',
    fontSize: '1.1rem'
  };

  const inputStyle = {
    width: '100%',
    padding: '12px',
    border: '2px solid #003366',
    borderRadius: '10px',
    fontSize: '16px',
    backgroundColor: 'white'
  };

  const ingredientRowStyle = {
    display: 'flex',
    gap: '10px',
    marginBottom: '10px',
    alignItems: 'center',
    flexWrap: 'wrap'
  };

  const instructionRowStyle = {
    display: 'flex',
    gap: '10px',
    marginBottom: '10px',
    alignItems: 'flex-start'
  };

  const buttonStyle = {
    padding: '8px 16px',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '500'
  };

  const addButtonStyle = {
    ...buttonStyle,
    backgroundColor: '#28a745',
    color: 'white',
    marginTop: '10px'
  };

  const removeButtonStyle = {
    ...buttonStyle,
    backgroundColor: '#dc3545',
    color: 'white',
    padding: '8px 12px'
  };

  const submitButtonStyle = {
    width: '100%',
    padding: '15px',
    backgroundColor: loading ? '#ccc' : '#003366',
    color: 'white',
    border: 'none',
    borderRadius: '10px',
    fontSize: '18px',
    fontWeight: '500',
    cursor: loading ? 'not-allowed' : 'pointer',
    transition: 'all 0.3s ease'
  };

  const stepNumberStyle = {
    backgroundColor: '#003366',
    color: 'white',
    borderRadius: '50%',
    width: '24px',
    height: '24px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '12px',
    fontWeight: 'bold',
    marginTop: '8px',
    flexShrink: 0
  };

  // Render guard
  if (!isAuthenticated()) {
    return null;
  }

  return (
    <div style={containerStyle}>
      <div style={formContainerStyle}>
        <h1 style={titleStyle}>➕ Add New Recipe</h1>

        {/* Error Message */}
        {error && (
          <div style={{
            background: '#f8d7da',
            color: '#721c24',
            padding: '1rem',
            borderRadius: '8px',
            marginBottom: '1rem',
            border: '1px solid #f5c6cb'
          }}>
            {error}
          </div>
        )}

        {/* Success Message */}
        {success && (
          <div style={{
            background: '#d4edda',
            color: '#155724',
            padding: '1rem',
            borderRadius: '8px',
            marginBottom: '1rem',
            border: '1px solid #c3e6cb'
          }}>
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Recipe Name */}
          <div style={{ marginBottom: '2rem' }}>
            <label style={labelStyle}>Recipe Name</label>
            <input
              type="text"
              name="recipe_name"
              value={formData.recipe_name}
              onChange={handleInputChange}
              style={inputStyle}
              placeholder="Enter recipe name"
              required
            />
          </div>

          {/* Ingredients Section */}
          <div style={{ marginBottom: '2rem' }}>
            <label style={labelStyle}>Ingredients</label>

            {ingredients.map((ingredient, index) => (
              <div key={index} style={ingredientRowStyle}>
                <input
                  type="text"
                  value={typeof ingredient.quantity === 'number'
                    ? formatQuantity(ingredient.quantity)
                    : ingredient.quantity}
                  onChange={(e) => handleIngredientChange(index, 'quantity', e.target.value)}
                  onKeyDown={(e) => handleIngredientKeyDown(index, 'quantity', e)}
                  onBlur={() => handleIngredientBlur(index, 'quantity')}
                  data-ingredient-index={index}
                  data-field="quantity"
                  style={{
                    width: '100px',
                    padding: '8px',
                    border: validateQuantity(ingredient.quantity) ? '2px solid #003366' : '2px solid #dc3545',
                    borderRadius: '8px',
                    fontSize: '14px'
                  }}
                  placeholder="Qty"
                />

                <select
                  value={ingredient.unit}
                  onChange={(e) => handleIngredientChange(index, 'unit', e.target.value)}
                  data-ingredient-index={index}
                  data-field="unit"
                  style={{
                    width: '120px',
                    padding: '8px',
                    border: '2px solid #003366',
                    borderRadius: '8px',
                    fontSize: '14px',
                    backgroundColor: 'white'
                  }}
                >
                  {availableUnits.map(unit => (
                    <option key={unit} value={unit}>{unit}</option>
                  ))}
                </select>

                <input
                  type="text"
                  value={ingredient.name}
                  onChange={(e) => handleIngredientChange(index, 'name', e.target.value)}
                  onKeyDown={(e) => handleIngredientKeyDown(index, 'name', e)}
                  onBlur={() => handleIngredientBlur(index, 'name')}
                  data-ingredient-index={index}
                  data-field="name"
                  style={{
                    flex: 1,
                    minWidth: '200px',
                    padding: '8px',
                    border: '2px solid #003366',
                    borderRadius: '8px',
                    fontSize: '14px'
                  }}
                  placeholder="Ingredient name (press Enter to add next)"
                />

                {ingredients.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeIngredient(index)}
                    style={removeButtonStyle}
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}

            <button
              type="button"
              onClick={addIngredient}
              style={addButtonStyle}
            >
              ➕ Add Ingredient
            </button>
          </div>

          {/* Instructions Section */}
          <div style={{ marginBottom: '2rem' }}>
            <label style={labelStyle}>Instructions</label>

            {instructions.map((instruction, index) => (
              <div key={index} style={instructionRowStyle}>
                <span style={stepNumberStyle}>{index + 1}</span>

                <textarea
                  value={instruction}
                  onChange={(e) => handleInstructionChange(index, e.target.value)}
                  onKeyDown={(e) => handleInstructionKeyDown(index, e)}
                  onBlur={() => handleInstructionBlur(index)}
                  data-instruction-index={index}
                  style={{
                    flex: 1,
                    padding: '8px',
                    border: '2px solid #003366',
                    borderRadius: '8px',
                    fontSize: '14px',
                    minHeight: '60px',
                    resize: 'vertical'
                  }}
                  placeholder={`Step ${index + 1} instructions... (Enter = next step, Shift+Enter = new line)`}
                />

                {instructions.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeInstruction(index)}
                    style={{
                      ...removeButtonStyle,
                      marginTop: '8px'
                    }}
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}

            <button
              type="button"
              onClick={addInstruction}
              style={addButtonStyle}
            >
              ➕ Add Step
            </button>
          </div>

          {/* Serving Size and Genre */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '1rem',
            marginBottom: '2rem'
          }}>
            <div>
              <label style={{ ...labelStyle, fontSize: '1rem' }}>
                Serving Size
              </label>
              <input
                type="number"
                name="serving_size"
                value={formData.serving_size}
                onChange={handleInputChange}
                min="1"
                style={inputStyle}
              />
            </div>

            <div>
              <label style={{ ...labelStyle, fontSize: '1rem' }}>
                Category
              </label>
              <select
                name="genre"
                value={formData.genre}
                onChange={handleInputChange}
                style={inputStyle}
              >
                {availableGenres.map(genre => (
                  <option key={genre} value={genre}>
                    {genre.charAt(0).toUpperCase() + genre.slice(1)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            style={submitButtonStyle}
          >
            {loading ? 'Creating Recipe...' : '🍳 Create Recipe'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AddRecipe;