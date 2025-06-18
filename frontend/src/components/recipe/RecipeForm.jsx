import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import axios from 'axios';
import { Fraction } from 'fraction.js';


const RecipeForm = ({ editMode = false, existingRecipe = null, onSubmitSuccess }) => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Form state
  const [formData, setFormData] = useState({
    recipe_name: '',
    serving_size: 1,
    genre: 'dinner',
    prep_time: 0,
    cook_time: 0
  });

  const [ingredients, setIngredients] = useState([
    { name: '', quantity: '', unit: 'cup' }
  ]);

  const [instructions, setInstructions] = useState(['']);

  // Add notes state
  const [notes, setNotes] = useState(['']);

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

  // Check for duplicate recipe in sessionStorage
  useEffect(() => {
    // Check if we're duplicating a recipe from sessionStorage
    const duplicateRecipeStr = sessionStorage.getItem('duplicateRecipe');
    console.log('Checking for duplicated recipe:', duplicateRecipeStr);

    if (duplicateRecipeStr) {
      try {
        const duplicateRecipe = JSON.parse(duplicateRecipeStr);
        console.log('Found duplicated recipe to load:', duplicateRecipe);

        setFormData({
          recipe_name: duplicateRecipe.recipe_name,
          serving_size: duplicateRecipe.serving_size,
          genre: duplicateRecipe.genre,
          prep_time: duplicateRecipe.prep_time || 0,
          cook_time: duplicateRecipe.cook_time || 0
        });

        setIngredients(duplicateRecipe.ingredients.map(ing => ({
          name: ing.name,
          quantity: ing.quantity,
          unit: ing.unit
        })));

        setInstructions([...duplicateRecipe.instructions]);

        if (duplicateRecipe.notes && duplicateRecipe.notes.length > 0) {
          setNotes([...duplicateRecipe.notes]);
        } else {
          setNotes(['']);
        }

        // Only remove from sessionStorage after successfully loading
        // This helps for debugging and retries if needed
        // sessionStorage.removeItem('duplicateRecipe');
      } catch (error) {
        console.error('Error parsing duplicated recipe:', error);
      }
    }
  }, []);

  // Handle edit mode separately
  useEffect(() => {
    if (editMode && existingRecipe) {
      setFormData({
        recipe_name: existingRecipe.recipe_name,
        serving_size: existingRecipe.serving_size,
        genre: existingRecipe.genre,
        prep_time: existingRecipe.prep_time || 0,
        cook_time: existingRecipe.cook_time || 0
      });

      setIngredients(existingRecipe.ingredients.map(ing => ({
        name: ing.name,
        quantity: ing.quantity,
        unit: ing.unit
      })));

      setInstructions([...existingRecipe.instructions]);

      // Add this part to load notes
      if (existingRecipe.notes && existingRecipe.notes.length > 0) {
        setNotes([...existingRecipe.notes]);
      } else {
        setNotes(['']);
      }
    }
  }, [editMode, existingRecipe]);

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

  const isValidFractionInput = (input) => {
    // Handle non-string or undefined inputs
    if (input === undefined || input === null) return true;

    // Convert to string to ensure we can use string methods
    const inputStr = String(input);

    // Empty string is valid
    if (inputStr === '') return true;

    // Check if it's a simple number
    if (!isNaN(inputStr) && !inputStr.includes('/')) return true;

    // Allow partial fractions (during typing)
    if (inputStr === '/') return true;
    if (/^\d+\/$/.test(inputStr)) return true;  // "1/"
    if (/^\/\d+$/.test(inputStr)) return true;  // "/2"

    // Whole number with partial fraction
    if (/^\d+ \d+\/$/.test(inputStr)) return true;  // "1 1/"
    if (/^\d+ \/\d+$/.test(inputStr)) return true;  // "1 /2"
    if (/^\d+ $/.test(inputStr)) return true;  // "1 " (space after number)

    // Check for valid complete fractions
    try {
      if (inputStr.includes('/')) {
        // Mixed number with fraction
        if (inputStr.includes(' ')) {
          const [whole, fraction] = inputStr.split(' ');
          if (isNaN(whole)) return false;

          if (!fraction.includes('/')) return true; // "1 2" is valid during typing

          const [num, denom] = fraction.split('/');
          return !isNaN(num) && (!denom || !isNaN(denom));
        }

        // Simple fraction
        const [num, denom] = inputStr.split('/');
        return (!num || !isNaN(num)) && (!denom || !isNaN(denom));
      }

      // Just a number
      return !isNaN(inputStr);
    } catch (e) {
      return false;
    }
  };

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

        // Check if we have a valid fraction part
        if (!denominator || parseInt(denominator) === 0) {
          return stringValue; // Return as is if not fully formed
        }

        return parseFloat(whole) + (parseFloat(numerator) / parseFloat(denominator));
      }

      // Handle simple fractions (e.g., "1/2")
      const [numerator, denominator] = stringValue.split('/');

      // Check if we have a valid denominator
      if (!denominator || parseInt(denominator) === 0) {
        return stringValue; // Return as is if not fully formed
      }

      return parseFloat(numerator) / parseFloat(denominator);
    } catch (e) {
      console.error("Error parsing fraction:", e);
      return value;
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
      if (isValidFractionInput(value)) {
        // Store the value as-is
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

      // Create a new ingredient row and insert it after the current one
      const newIngredients = [...ingredients];
      newIngredients.splice(index + 1, 0, { name: '', quantity: '', unit: 'cup' });
      setIngredients(newIngredients);

      // Focus the quantity field of the new row after a short delay
      setTimeout(() => {
        const nextQuantityInput = document.querySelector(`input[data-ingredient-index="${index + 1}"][data-field="quantity"]`);
        if (nextQuantityInput) nextQuantityInput.focus();
      }, 100);
    }
  };

  const handleIngredientBlur = (index, field) => {
    // Format quantities as fractions on blur
    if (field === 'quantity') {
      const value = ingredients[index].quantity;

      // Skip empty values or already numeric values
      if (!value || typeof value === 'number') return;

      if (isValidFractionInput(value)) {
        const newIngredients = [...ingredients];
        // Only parse complete fractions
        if (typeof value === 'string' && value.includes('/') &&
            !(value === '/' || value.endsWith('/') || value.startsWith('/'))) {
          try {
            const parsedValue = parseQuantity(value);
            if (typeof parsedValue === 'number' && !isNaN(parsedValue)) {
              newIngredients[index].quantity = parsedValue;
              setIngredients(newIngredients);
            }
          } catch (e) {
            console.error("Error parsing fraction on blur:", e);
          }
        }
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

  // Move instruction up or down
  const moveInstruction = (index, direction) => {
    if (
      (direction === 'up' && index === 0) ||
      (direction === 'down' && index === instructions.length - 1)
    ) {
      return; // Cannot move beyond array bounds
    }

    const newIndex = direction === 'up' ? index - 1 : index + 1;
    const newInstructions = [...instructions];

    // Swap the instructions
    [newInstructions[index], newInstructions[newIndex]] =
    [newInstructions[newIndex], newInstructions[index]];

    setInstructions(newInstructions);
  };

  // Change step number (reorder)
  const changeStepNumber = (oldIndex, newStepNumber) => {
    const newIndex = newStepNumber - 1; // Convert from 1-based to 0-based

    // Validate the new index
    if (newIndex < 0 || newIndex >= instructions.length || newIndex === oldIndex) {
      return; // Invalid index or no change needed
    }

    const newInstructions = [...instructions];
    const movedInstruction = newInstructions[oldIndex];

    // Remove the instruction from its current position
    newInstructions.splice(oldIndex, 1);

    // Insert at the new position
    newInstructions.splice(newIndex, 0, movedInstruction);

    setInstructions(newInstructions);
  };

  const handleInstructionKeyDown = (index, e) => {
    if (e.key === 'Enter' && e.shiftKey === false) {
      e.preventDefault();

      // Create a new instruction row and insert it after the current one
      const newInstructions = [...instructions];
      newInstructions.splice(index + 1, 0, ''); // Insert empty string at index+1
      setInstructions(newInstructions);

      // Focus the newly created instruction field after a short delay
      setTimeout(() => {
        const nextTextarea = document.querySelector(`textarea[data-instruction-index="${index + 1}"]`);
        if (nextTextarea) nextTextarea.focus();
      }, 100);
    }
  };

  const handleInstructionBlur = (index) => {
    // Auto-add new instruction row if this is the last one and has content
    if (index === instructions.length - 1 && instructions[index].trim()) {
      setTimeout(() => addInstruction(), 100);
    }
  };

  // Note handlers
  const handleNoteChange = (index, value) => {
    const newNotes = [...notes];
    newNotes[index] = value;
    setNotes(newNotes);
  };

  const addNote = () => {
    setNotes([...notes, '']);
  };

  const removeNote = (index) => {
    if (notes.length > 1) {
      const newNotes = notes.filter((_, i) => i !== index);
      setNotes(newNotes);
    }
  };

  // Move note up or down
  const moveNote = (index, direction) => {
    if (
      (direction === 'up' && index === 0) ||
      (direction === 'down' && index === notes.length - 1)
    ) {
      return; // Cannot move beyond array bounds
    }

    const newIndex = direction === 'up' ? index - 1 : index + 1;
    const newNotes = [...notes];

    // Swap the notes
    [newNotes[index], newNotes[newIndex]] =
    [newNotes[newIndex], newNotes[index]];

    setNotes(newNotes);
  };

  // Change note number (reorder)
  const changeNoteNumber = (oldIndex, newNoteNumber) => {
    const newIndex = newNoteNumber - 1; // Convert from 1-based to 0-based

    // Validate the new index
    if (newIndex < 0 || newIndex >= notes.length || newIndex === oldIndex) {
      return; // Invalid index or no change needed
    }

    const newNotes = [...notes];
    const movedNote = newNotes[oldIndex];

    // Remove the note from its current position
    newNotes.splice(oldIndex, 1);

    // Insert at the new position
    newNotes.splice(newIndex, 0, movedNote);

    setNotes(newNotes);
  };

  const handleNoteKeyDown = (index, e) => {
    if (e.key === 'Enter' && e.shiftKey === false) {
      e.preventDefault();

      // Create a new note row and insert it after the current one
      const newNotes = [...notes];
      newNotes.splice(index + 1, 0, ''); // Insert empty string at index+1
      setNotes(newNotes);

      // Focus the newly created note field after a short delay
      setTimeout(() => {
        const nextTextarea = document.querySelector(`textarea[data-note-index="${index + 1}"]`);
        if (nextTextarea) nextTextarea.focus();
      }, 100);
    }
  };

  const handleNoteBlur = (index) => {
    // Auto-add new note row if this is the last one and has content
    if (index === notes.length - 1 && notes[index].trim()) {
      setTimeout(() => addNote(), 100);
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

    // Filter valid notes
    const validNotes = notes.filter(note => note.trim());

    try {
      // Prepare the ingredients with parsed quantities
      const processedIngredients = validIngredients.map(ing => {
        // Parse the quantity to a float for submission
        let qty = ing.quantity;
        if (typeof qty === 'string') {
          const parsed = parseQuantity(qty);
          if (typeof parsed === 'number' && !isNaN(parsed)) {
            qty = parsed;
          }
        }

        return {
          name: ing.name.trim(),
          quantity: parseFloat(qty),
          unit: ing.unit
        };
      });

      const recipeData = {
        recipe_name: formData.recipe_name.trim(),
        serving_size: parseInt(formData.serving_size),
        genre: formData.genre,
        prep_time: parseInt(formData.prep_time || 0),
        cook_time: parseInt(formData.cook_time || 0),
        ingredients: processedIngredients,
        instructions: validInstructions.map(inst => inst.trim()),
        notes: validNotes.map(note => note.trim()) // Add notes field
      };

      // Check if this is a duplication attempt by checking URL parameters
      const urlParams = new URLSearchParams(location.search);
      const isDuplicating = urlParams.get('duplicate') === 'true';

      // If duplicating, check if any changes were made compared to the original
      if (isDuplicating) {
        // Get the original recipe from sessionStorage (might be null if page was refreshed)
        const originalRecipeStr = sessionStorage.getItem('originalRecipe');

        // If we still have the original recipe data, compare to prevent exact duplicates
        if (originalRecipeStr) {
          try {
            const originalRecipe = JSON.parse(originalRecipeStr);

            // Remove the "(Copy)" suffix for comparison
            const nameWithoutCopy = recipeData.recipe_name.replace(' (Copy)', '').trim();

            // Check if this is an exact duplicate (excluding the recipe name)
            const isExactDuplicate =
              nameWithoutCopy === originalRecipe.recipe_name &&
              recipeData.serving_size === originalRecipe.serving_size &&
              recipeData.genre === originalRecipe.genre &&
              recipeData.prep_time === originalRecipe.prep_time &&
              recipeData.cook_time === originalRecipe.cook_time &&
              JSON.stringify(recipeData.ingredients) === JSON.stringify(originalRecipe.ingredients) &&
              JSON.stringify(recipeData.instructions) === JSON.stringify(originalRecipe.instructions) &&
              JSON.stringify(recipeData.notes) === JSON.stringify(originalRecipe.notes || []);

            if (isExactDuplicate) {
              setError('You must make at least one change to create a variant of this recipe.');
              setLoading(false);
              return;
            }
          } catch (error) {
            console.error('Error comparing recipes:', error);
            // Continue with save if comparison fails
          }
        }

        // Clean up after comparison
        sessionStorage.removeItem('originalRecipe');
      }

      let response;

      if (editMode && existingRecipe) {
        // Update existing recipe
        console.log('Updating recipe:', recipeData);
        response = await axios.put(`http://127.0.0.1:8000/recipes/${existingRecipe.id}`, recipeData);
        setSuccess('Recipe updated successfully! 🎉');
      } else {
        // Create new recipe
        console.log('Creating recipe:', recipeData);
        response = await axios.post('http://127.0.0.1:8000/recipes', recipeData);
        setSuccess('Recipe created successfully! 🎉');

        // Reset form for new recipe
        setFormData({ recipe_name: '', serving_size: 1, genre: 'dinner', prep_time: 0, cook_time: 0 });
        setIngredients([{ name: '', quantity: '', unit: 'cup' }]);
        setInstructions(['']);
        setNotes(['']);
      }

      // Call the callback if provided
      if (onSubmitSuccess) {
        onSubmitSuccess(response.data);
      }

      // Redirect after a short delay if not in edit mode
      if (!editMode) {
        setTimeout(() => {
          navigate('/recipes');
        }, 2000);
      }

    } catch (error) {
      console.error('Error saving recipe:', error);
      setError(error.response?.data?.detail || 'Failed to save recipe');
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
        <h1 style={titleStyle}>{editMode ? '✏️ Edit Recipe' : '➕ Add New Recipe'}</h1>

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
                    border: isValidFractionInput(ingredient.quantity) ? '2px solid #003366' : '2px solid #dc3545',
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
                  onBlur={() => handleIngredientBlur(index)}
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
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '4px'
                }}>
                  {/* Up arrow */}
                  <button
                    type="button"
                    onClick={() => moveInstruction(index, 'up')}
                    disabled={index === 0}
                    style={{
                      padding: '2px',
                      backgroundColor: 'transparent',
                      border: 'none',
                      cursor: index === 0 ? 'not-allowed' : 'pointer',
                      color: index === 0 ? '#ccc' : '#003366',
                      fontSize: '14px',
                      width: '24px',
                      height: '24px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                    title="Move step up"
                  >
                    ▲
                  </button>

                  {/* Step number - clickable for reordering */}
                  <div
                    style={{
                      backgroundColor: '#003366',
                      color: 'white',
                      borderRadius: '50%',
                      width: '28px',
                      height: '28px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '14px',
                      fontWeight: 'bold',
                      cursor: 'pointer',
                      position: 'relative',
                    }}
                    onClick={() => {
                      const newStep = prompt(`Change step ${index + 1} to position:`, index + 1);
                      if (newStep && !isNaN(newStep) && newStep > 0 && newStep <= instructions.length) {
                        changeStepNumber(index, parseInt(newStep));
                      }
                    }}
                    title="Click to change step position"
                  >
                    {index + 1}
                  </div>

                  {/* Down arrow */}
                  <button
                    type="button"
                    onClick={() => moveInstruction(index, 'down')}
                    disabled={index === instructions.length - 1}
                    style={{
                      padding: '2px',
                      backgroundColor: 'transparent',
                      border: 'none',
                      cursor: index === instructions.length - 1 ? 'not-allowed' : 'pointer',
                      color: index === instructions.length - 1 ? '#ccc' : '#003366',
                      fontSize: '14px',
                      width: '24px',
                      height: '24px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                    title="Move step down"
                  >
                    ▼
                  </button>
                </div>

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

          {/* Notes Section */}
          <div style={{ marginBottom: '2rem' }}>
            <label style={labelStyle}>Notes (Optional)</label>

            {notes.map((note, index) => (
              <div key={index} style={instructionRowStyle}>
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '4px'
                }}>
                  {/* Up arrow */}
                  <button
                    type="button"
                    onClick={() => moveNote(index, 'up')}
                    disabled={index === 0}
                    style={{
                      padding: '2px',
                      backgroundColor: 'transparent',
                      border: 'none',
                      cursor: index === 0 ? 'not-allowed' : 'pointer',
                      color: index === 0 ? '#ccc' : '#6c757d',
                      fontSize: '14px',
                      width: '24px',
                      height: '24px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                    title="Move note up"
                  >
                    ▲
                  </button>

                  {/* Note number - clickable for reordering */}
                  <div
                    style={{
                      backgroundColor: '#6c757d', // Different color for notes
                      color: 'white',
                      borderRadius: '50%',
                      width: '28px',
                      height: '28px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '14px',
                      fontWeight: 'bold',
                      cursor: 'pointer',
                      position: 'relative',
                    }}
                    onClick={() => {
                      const newNote = prompt(`Change note ${index + 1} to position:`, index + 1);
                      if (newNote && !isNaN(newNote) && newNote > 0 && newNote <= notes.length) {
                        changeNoteNumber(index, parseInt(newNote));
                      }
                    }}
                    title="Click to change note position"
                  >
                    {index + 1}
                  </div>

                  {/* Down arrow */}
                  <button
                    type="button"
                    onClick={() => moveNote(index, 'down')}
                    disabled={index === notes.length - 1}
                    style={{
                      padding: '2px',
                      backgroundColor: 'transparent',
                      border: 'none',
                      cursor: index === notes.length - 1 ? 'not-allowed' : 'pointer',
                      color: index === notes.length - 1 ? '#ccc' : '#6c757d',
                      fontSize: '14px',
                      width: '24px',
                      height: '24px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                    title="Move note down"
                  >
                    ▼
                  </button>
                </div>

                <textarea
                  value={note}
                  onChange={(e) => handleNoteChange(index, e.target.value)}
                  onKeyDown={(e) => handleNoteKeyDown(index, e)}
                  onBlur={() => handleNoteBlur(index)}
                  data-note-index={index}
                  style={{
                    flex: 1,
                    padding: '8px',
                    border: '2px solid #6c757d', // Different border color
                    borderRadius: '8px',
                    fontSize: '14px',
                    minHeight: '60px',
                    resize: 'vertical'
                  }}
                  placeholder={`Note ${index + 1}... (Enter = next note, Shift+Enter = new line)`}
                />

                {notes.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeNote(index)}
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
              onClick={addNote}
              style={{
                ...addButtonStyle,
                backgroundColor: '#6c757d' // Different color
              }}
            >
              ➕ Add Note
            </button>
          </div>

          {/* Serving Size, Genre, and Time Inputs */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
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
                    {formatGenreName(genre)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ ...labelStyle, fontSize: '1rem' }}>
                Prep Time (mins)
              </label>
              <input
                type="number"
                name="prep_time"
                value={formData.prep_time}
                onChange={handleInputChange}
                min="0"
                style={{
                  ...inputStyle,
                  width: '100px',
                  padding: '10px',
                  textAlign: 'center'
                }}
              />
            </div>

            <div>
              <label style={{ ...labelStyle, fontSize: '1rem' }}>
                Cook Time (mins)
              </label>
              <input
                type="number"
                name="cook_time"
                value={formData.cook_time}
                onChange={handleInputChange}
                min="0"
                style={{
                  ...inputStyle,
                  width: '100px',
                  padding: '10px',
                  textAlign: 'center'
                }}
              />
            </div>

            <div>
              <label style={{
                ...labelStyle,
                fontSize: '1rem',
                fontWeight: '600',
                color: '#002855'
              }}>
                Total Time (mins)
              </label>
              <div style={{
                ...inputStyle,
                width: '100px',
                padding: '10px',
                textAlign: 'center',
                fontWeight: '600',
                backgroundColor: '#f0f8ff',
                border: '2px solid #002855'
              }}>
                {parseInt(formData.prep_time || 0) + parseInt(formData.cook_time || 0)}
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            style={submitButtonStyle}
          >
            {loading
              ? (editMode ? 'Saving Recipe...' : 'Creating Recipe...')
              : (editMode ? '💾 Save Recipe' : '🍳 Create Recipe')}
          </button>
        </form>
      </div>
    </div>
  );
};

export default RecipeForm;