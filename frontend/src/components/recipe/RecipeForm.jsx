// RecipeForm.jsx - Fixed version with proper FormData handling
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import axios from 'axios';

// Format genre display name
const formatGenreName = (genre) => {
  if (!genre) return '';

  // Standard capitalization for genres
  return genre.charAt(0).toUpperCase() + genre.slice(1);
};

// Format dietary restriction display name
const formatDietaryRestrictionName = (restriction) => {
  if (!restriction) return '';

  switch(restriction) {
    case 'gluten_free': return 'Gluten Free';
    case 'dairy_free': return 'Dairy Free';
    case 'egg_free': return 'Egg Free';
    default:
      return restriction.charAt(0).toUpperCase() + restriction.slice(1);
  }
};

const RecipeForm = ({ editMode = false, existingRecipe = null, onSubmitSuccess }) => {
  const { isAuthenticated, apiBaseUrl } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  // Form state
  const [formData, setFormData] = useState({
    recipe_name: '',
    description: '',
    serving_size: 1,
    genre: 'dinner',
    prep_time: 0,
    cook_time: 0,
    dietary_restrictions: []
  });

  const [ingredients, setIngredients] = useState([
    { name: '', quantity: '', unit: 'cup' }
  ]);

  const [instructions, setInstructions] = useState(['']);

  // Add notes state
  const [notes, setNotes] = useState(['']);

  // Photo state
  const [photoFile, setPhotoFile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const [showCamera, setShowCamera] = useState(false);
  const [cameraStream, setCameraStream] = useState(null);
  const [cameraError, setCameraError] = useState('');

  // Options state
  const [availableUnits, setAvailableUnits] = useState([
    'cup', 'cups', 'tablespoon', 'tablespoons', 'teaspoon', 'teaspoons',
    'ounce', 'ounces', 'pound', 'pounds', 'gram', 'grams',
    'kilogram', 'kilograms', 'liter', 'liters', 'milliliter', 'milliliters',
    'piece', 'pieces', 'whole', 'stick', 'sticks', 'pinch', 'dash'
  ]);

  const [availableGenres, setAvailableGenres] = useState([
    'breakfast', 'lunch', 'dinner', 'snack', 'dessert', 'appetizer'
  ]);

  // Available dietary restrictions
  const availableDietaryRestrictions = [
    'gluten_free', 'dairy_free', 'egg_free'
  ];

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoadingTempRecipe, setIsLoadingTempRecipe] = useState(false);

  // Authentication check
  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/login');
    }
  }, [isAuthenticated, navigate]);

  // Cleanup camera stream on unmount
  useEffect(() => {
    return () => {
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
      }
    };
  }, [cameraStream]);

  // Photo handling functions
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && file.type.startsWith('image/')) {
      setPhotoFile(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setPhotoPreview(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const startCamera = async () => {
    try {
      setCameraError('');
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' } // Use rear camera if available
      });
      setCameraStream(stream);
      setShowCamera(true);

      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      }, 100);
    } catch (err) {
      console.error('Error accessing camera:', err);
      setCameraError('Unable to access camera. Please check permissions or use file upload instead.');
    }
  };

  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const canvas = canvasRef.current;
      const video = videoRef.current;

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0);

      canvas.toBlob((blob) => {
        const file = new File([blob], 'recipe-photo.jpg', { type: 'image/jpeg' });
        setPhotoFile(file);
        setPhotoPreview(canvas.toDataURL());
        stopCamera();
      }, 'image/jpeg', 0.8);
    }
  };

  const stopCamera = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach(track => track.stop());
      setCameraStream(null);
    }
    setShowCamera(false);
  };

  const removePhoto = () => {
    setPhotoFile(null);
    setPhotoPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // NEW: Handle AI recipe auto-population from temp_id
  useEffect(() => {
    const loadTempRecipe = async () => {
      const urlParams = new URLSearchParams(location.search);
      const tempId = urlParams.get('temp_id');

      if (tempId) {
        setIsLoadingTempRecipe(true);

        try {
          const response = await axios.get(`${apiBaseUrl}/temp-recipe/${tempId}`);
          const tempRecipeData = response.data.recipe_data;



          if (tempRecipeData) {
            // Populate form with AI recipe data
            setFormData({
              recipe_name: tempRecipeData.recipe_name || '',
              description: tempRecipeData.description || '',
              serving_size: tempRecipeData.serving_size || 1,
              genre: tempRecipeData.genre || 'dinner',
              prep_time: tempRecipeData.prep_time || 0,
              cook_time: tempRecipeData.cook_time || 0,
              dietary_restrictions: tempRecipeData.dietary_restrictions || []
            });

            // Populate ingredients
            if (tempRecipeData.ingredients && tempRecipeData.ingredients.length > 0) {
              setIngredients(tempRecipeData.ingredients.map(ing => ({
                name: ing.name || '',
                quantity: ing.quantity || '',
                unit: ing.unit || 'cup'
              })));
            }

            // Populate instructions
            if (tempRecipeData.instructions && tempRecipeData.instructions.length > 0) {
              setInstructions([...tempRecipeData.instructions]);
            }

            // Populate notes
            if (tempRecipeData.notes && tempRecipeData.notes.length > 0) {
              setNotes([...tempRecipeData.notes]);
            }

            setSuccess('✨ Recipe from Ralph loaded successfully! Review and modify as needed.');
          }
        } catch (error) {
          console.error('Error loading temp recipe:', error);
          if (error.response?.status === 404) {
            setError('The recipe link has expired. Please ask Ralph for a new recipe suggestion.');
          } else {
            setError('Failed to load recipe data. Please try asking Ralph again.');
          }
        } finally {
          setIsLoadingTempRecipe(false);
        }
      }
    };

    // Only load temp recipe if not in edit mode
    if (!editMode) {
      loadTempRecipe();
    }
  }, [location.search, editMode, apiBaseUrl]);

  // Handle edit mode separately
  useEffect(() => {

    if (editMode && existingRecipe) {
      console.log('Setting form data from existing recipe:', {
        recipeName: existingRecipe.recipe_name,
        description: existingRecipe.description,
        hasDescription: !!existingRecipe.description
      });

      setFormData({
        recipe_name: existingRecipe.recipe_name,
        description: existingRecipe.description || '',
        serving_size: existingRecipe.serving_size,
        genre: existingRecipe.genre,
        prep_time: existingRecipe.prep_time || 0,
        cook_time: existingRecipe.cook_time || 0,
        dietary_restrictions: existingRecipe.dietary_restrictions || []
      });

      setIngredients(existingRecipe.ingredients.map(ing => ({
        name: ing.name,
        quantity: ing.quantity,
        unit: ing.unit
      })));

      setInstructions([...existingRecipe.instructions]);

      if (existingRecipe.notes && existingRecipe.notes.length > 0) {
        setNotes([...existingRecipe.notes]);
      } else {
        setNotes(['']);
      }

      // Load existing photo if available
      if (existingRecipe.photo_url && existingRecipe.photo_url.trim()) {
        setPhotoPreview(existingRecipe.photo_url);
      }

    }
  }, [editMode, existingRecipe]);

  // Handle duplication (separate from AI temp recipes)
  useEffect(() => {
    console.log('Duplication useEffect running:', { editMode });

    // Skip this effect if in edit mode or if we're loading a temp recipe
    if (editMode) {
      console.log('Skipping duplication useEffect because in edit mode');
      return;
    }

    const urlParams = new URLSearchParams(location.search);
    const isDuplicating = urlParams.get('duplicate') === 'true';
    const hasTempId = urlParams.get('temp_id');

    // Only handle duplication if there's no temp_id (AI recipe)
    if (isDuplicating && !hasTempId) {
      console.log('Handling duplication (not AI recipe)');

      const duplicateRecipeStr = sessionStorage.getItem('duplicateRecipe');
      console.log('Duplicating - checking for duplicated recipe:', duplicateRecipeStr ? 'Found' : 'Not found');

      if (duplicateRecipeStr) {
        try {
          const duplicateRecipe = JSON.parse(duplicateRecipeStr);
          console.log('Found duplicated recipe to load:', duplicateRecipe);

          setFormData({
            recipe_name: duplicateRecipe.recipe_name,
            description: duplicateRecipe.description || '',
            serving_size: duplicateRecipe.serving_size,
            genre: duplicateRecipe.genre,
            prep_time: duplicateRecipe.prep_time || 0,
            cook_time: duplicateRecipe.cook_time || 0,
            dietary_restrictions: duplicateRecipe.dietary_restrictions || []
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
        } catch (error) {
          console.error('Error parsing duplicated recipe:', error);
        }
      }
    } else if (!isDuplicating && !hasTempId) {
      // NOT duplicating and no temp_id - clear sessionStorage and reset to blank form
      console.log('Not duplicating and no temp_id - clearing sessionStorage and resetting form');
      sessionStorage.removeItem('duplicateRecipe');
      sessionStorage.removeItem('originalRecipe');

      setFormData({
        recipe_name: '',
        description: '',
        serving_size: 1,
        genre: 'dinner',
        prep_time: 0,
        cook_time: 0,
        dietary_restrictions: []
      });

      setIngredients([{ name: '', quantity: '', unit: 'cup' }]);
      setInstructions(['']);
      setNotes(['']);
    }
  }, [location.search, editMode]);

  // Fetch options from API
  useEffect(() => {
  const fetchOptions = async () => {
    try {
      const [unitsRes, genresRes] = await Promise.all([
        axios.get(`${apiBaseUrl}/measuring-units`),
        axios.get(`${apiBaseUrl}/genres`)
      ]);

      // Use exact units from backend
      if (unitsRes.data.units) {
        setAvailableUnits(unitsRes.data.units);
        console.log('Available units from backend:', unitsRes.data.units);
      }

      // Filter out dietary restrictions from genres
      if (genresRes.data.genres) {
        const filteredGenres = genresRes.data.genres.filter(genre =>
          !['gluten_free', 'dairy_free', 'egg_free'].includes(genre)
        );
        setAvailableGenres(filteredGenres);
        console.log('Available genres from backend:', filteredGenres);
      }
    } catch (error) {
      console.error('Error fetching options:', error);
      // Keep default values if API fails - but log this
      console.warn('Using default units/genres due to API failure');
    }
  };

  if (isAuthenticated()) {
    fetchOptions();
  }
}, [isAuthenticated, apiBaseUrl]);

  // Fraction utilities - Robust
  const formatQuantity = (value) => {
    if (value === undefined || value === null || value === '') return '';

    try {
      // Convert to number first
      const numValue = typeof value === 'number' ? value : parseFloat(value);

      // Handle integer values
      if (Number.isInteger(numValue)) {
        return String(numValue);
      }

      // Use a more robust fraction conversion
      return convertDecimalToMixedNumber(numValue);
    } catch (e) {
      console.error("Error formatting fraction:", e);
      return String(value);
    }
  };

  const convertDecimalToMixedNumber = (decimal) => {
    try {
      // Handle edge cases
      if (decimal === 0) return "0";
      if (decimal < 0) return String(decimal); // Handle negative numbers as decimals

      // Get the whole number part
      const wholePart = Math.floor(decimal);
      const fractionalPart = decimal - wholePart;

      // If no fractional part, return whole number
      if (fractionalPart === 0) {
        return String(wholePart);
      }

      // Convert fractional part to fraction
      const fraction = decimalToFraction(fractionalPart);

      // Return appropriate format
      if (wholePart === 0) {
        return fraction; // Just the fraction (e.g., "1/2")
      } else {
        return `${wholePart} ${fraction}`; // Mixed number (e.g., "1 1/2")
      }
    } catch (e) {
      console.error("Error converting to mixed number:", e);
      return String(decimal);
    }
  };

  const decimalToFraction = (decimal) => {
    // Common fractions lookup for better accuracy
    const commonFractions = {
      0.125: "1/8",
      0.25: "1/4",
      0.375: "3/8",
      0.5: "1/2",
      0.625: "5/8",
      0.75: "3/4",
      0.875: "7/8",
      0.333: "1/3",
      0.667: "2/3",
      0.2: "1/5",
      0.4: "2/5",
      0.6: "3/5",
      0.8: "4/5"
    };

    // Check for common fractions first (with tolerance)
    for (const [dec, frac] of Object.entries(commonFractions)) {
      if (Math.abs(decimal - parseFloat(dec)) < 0.001) {
        return frac;
      }
    }

    // Use algorithm to find fraction
    let tolerance = 1e-6;
    let h1 = 1, h2 = 0, k1 = 0, k2 = 1;
    let b = decimal;

    do {
      let a = Math.floor(b);
      let aux = h1; h1 = a * h1 + h2; h2 = aux;
      aux = k1; k1 = a * k1 + k2; k2 = aux;
      b = 1 / (b - a);
    } while (Math.abs(decimal - h1 / k1) > decimal * tolerance);

    return `${h1}/${k1}`;
  };

  const isValidFractionInput = (input) => {
    if (input === undefined || input === null) return true;

    const inputStr = String(input).trim();
    if (inputStr === '') return true;

    // Allow simple numbers
    if (!isNaN(inputStr) && !inputStr.includes('/')) return true;

    // Allow partial input during typing
    if (inputStr === '/') return true;
    if (/^\d+\/$/.test(inputStr)) return true;  // "1/"
    if (/^\/\d+$/.test(inputStr)) return true;  // "/2"
    if (/^\d+ $/.test(inputStr)) return true;   // "1 " (space after number)
    if (/^\d+ \/$/.test(inputStr)) return true; // "1 /"
    if (/^\d+ \d+\/$/.test(inputStr)) return true; // "1 1/"

    // Validate complete fractions and mixed numbers
    try {
      // Simple fraction like "1/2"
      if (/^\d+\/\d+$/.test(inputStr)) {
        const [num, denom] = inputStr.split('/');
        return !isNaN(num) && !isNaN(denom) && parseInt(denom) !== 0;
      }

      // Mixed number like "1 1/2"
      if (/^\d+\s+\d+\/\d+$/.test(inputStr)) {
        const parts = inputStr.split(' ');
        const whole = parts[0];
        const [num, denom] = parts[1].split('/');
        return !isNaN(whole) && !isNaN(num) && !isNaN(denom) && parseInt(denom) !== 0;
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
      if (typeof value === 'number') return value;

      const stringValue = String(value).trim();

      // Handle simple numeric values
      if (!stringValue.includes('/')) {
        const parsed = parseFloat(stringValue);
        return isNaN(parsed) ? stringValue : parsed;
      }

      // Handle mixed numbers (e.g., "1 1/2")
      if (stringValue.includes(' ')) {
        const parts = stringValue.split(' ');
        if (parts.length !== 2) return stringValue;

        const whole = parseFloat(parts[0]);
        const fractionPart = parts[1];

        if (isNaN(whole) || !fractionPart.includes('/')) return stringValue;

        const [numerator, denominator] = fractionPart.split('/');
        const num = parseInt(numerator);
        const denom = parseInt(denominator);

        if (isNaN(num) || isNaN(denom) || denom === 0) return stringValue;

        return whole + (num / denom);
      }

      // Handle simple fractions (e.g., "1/2")
      const [numerator, denominator] = stringValue.split('/');
      const num = parseInt(numerator);
      const denom = parseInt(denominator);

      if (isNaN(num) || isNaN(denom) || denom === 0) return stringValue;

      return num / denom;
    } catch (e) {
      console.error("Error parsing quantity:", e);
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

  // Toggle dietary restriction
  const handleDietaryRestrictionChange = (restriction) => {
    const currentRestrictions = [...formData.dietary_restrictions];

    if (currentRestrictions.includes(restriction)) {
      // Remove if already included
      setFormData({
        ...formData,
        dietary_restrictions: currentRestrictions.filter(r => r !== restriction)
      });
    } else {
      // Add if not included
      setFormData({
        ...formData,
        dietary_restrictions: [...currentRestrictions, restriction]
      });
    }
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
    // Validate serving size
    const servingSize = parseInt(formData.serving_size);
    if (isNaN(servingSize) || servingSize <= 0 || servingSize > 100) {
      setError('Serving size must be a number between 1 and 100');
      setLoading(false);
      return;
    }

    // Validate prep and cook times
    const prepTime = parseInt(formData.prep_time || 0);
    const cookTime = parseInt(formData.cook_time || 0);
    if (prepTime < 0 || prepTime > 1440) {
      setError('Prep time must be between 0 and 1440 minutes');
      setLoading(false);
      return;
    }
    if (cookTime < 0 || cookTime > 1440) {
      setError('Cook time must be between 0 and 1440 minutes');
      setLoading(false);
      return;
    }

    // Validate recipe name length
    if (formData.recipe_name.trim().length > 200) {
      setError('Recipe name must be 200 characters or less');
      setLoading(false);
      return;
    }

    // Validate description length
    if (formData.description && formData.description.length > 500) {
      setError('Description must be 500 characters or less');
      setLoading(false);
      return;
    }

    // FIXED: Improved ingredient processing with better validation
    const processedIngredients = validIngredients.map((ing, index) => {
  // Parse the quantity to a float for submission
  let qty = ing.quantity;
  if (typeof qty === 'string') {
    const parsed = parseQuantity(qty);
    if (typeof parsed === 'number' && !isNaN(parsed)) {
      qty = parsed;
    } else {
      // If we can't parse it, try parseFloat as fallback
      qty = parseFloat(qty);
      if (isNaN(qty)) {
        throw new Error(`Invalid quantity for ingredient ${index + 1}: "${ing.quantity}". Please enter a valid number.`);
      }
    }
  }

  // Ensure quantity is a positive number
  const finalQuantity = parseFloat(qty);
  if (isNaN(finalQuantity) || finalQuantity <= 0) {
    throw new Error(`Invalid quantity for ingredient ${index + 1}: "${ing.quantity}". Quantity must be a positive number.`);
  }

  // Validate unit against allowed units
  const validUnits = [
    'cup', 'cups', 'tablespoon', 'tablespoons', 'teaspoon', 'teaspoons',
    'ounce', 'ounces', 'pound', 'pounds', 'gram', 'grams',
    'kilogram', 'kilograms', 'liter', 'liters', 'milliliter', 'milliliters',
    'piece', 'pieces', 'whole', 'stick', 'sticks', 'pinch', 'dash'
  ];

  if (!validUnits.includes(ing.unit)) {
    throw new Error(`Invalid unit for ingredient ${index + 1}: "${ing.unit}". Please select a valid unit from the dropdown.`);
  }

  // Validate ingredient name
  if (!ing.name || !ing.name.trim()) {
    throw new Error(`Ingredient ${index + 1} name is required.`);
  }

  return {
    name: ing.name.trim(),
    quantity: finalQuantity,
    unit: ing.unit
  };
});

    const recipeData = {
      recipe_name: formData.recipe_name.trim(),
      description: formData.description.trim() || null,
      serving_size: servingSize,
      genre: formData.genre,
      prep_time: prepTime,
      cook_time: cookTime,
      ingredients: processedIngredients,
      instructions: validInstructions.map(inst => inst.trim()),
      notes: validNotes.map(note => note.trim()),
      dietary_restrictions: formData.dietary_restrictions || []
    };

    // FIXED: Always use FormData for consistency with backend
    const formDataToSend = new FormData();
    formDataToSend.append('recipe_data', JSON.stringify(recipeData));

    // Add photo if present
    if (photoFile) {
      formDataToSend.append('photo', photoFile);
    }

    // Debug logging to help identify issues
    console.log('Sending recipe data:', recipeData);

    // Check if this is a duplication attempt by checking URL parameters
    const urlParams = new URLSearchParams(location.search);
    const isDuplicating = urlParams.get('duplicate') === 'true';
    const tempId = urlParams.get('temp_id'); // Check for AI recipe

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
            JSON.stringify(recipeData.notes) === JSON.stringify(originalRecipe.notes || []) &&
            JSON.stringify(recipeData.dietary_restrictions) === JSON.stringify(originalRecipe.dietary_restrictions || []);

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
      sessionStorage.removeItem('duplicateRecipe');
    }

    // If there's a temp_id, clean it up after successful submission
    if (tempId) {
      try {
        await axios.delete(`${apiBaseUrl}/temp-recipe/${tempId}`);
        console.log('Cleaned up temp recipe:', tempId);
      } catch (cleanupError) {
        console.warn('Could not clean up temp recipe:', cleanupError);
        // Don't fail the submission if cleanup fails
      }
    }

    let response;

    if (editMode && existingRecipe) {
      // Update existing recipe
      console.log('Updating recipe with FormData');
      response = await axios.put(`${apiBaseUrl}/recipes/${existingRecipe.id}`, formDataToSend);
      setSuccess('Recipe updated successfully! 🎉');
    } else {
      // Create new recipe
      console.log('Creating recipe with FormData');
      response = await axios.post(`${apiBaseUrl}/recipes`, formDataToSend);

      if (tempId) {
        setSuccess('✨ Recipe from Ralph saved successfully! 🎉');
      } else {
        setSuccess('Recipe created successfully! 🎉');
      }

      // Reset form for new recipe
      setFormData({
        recipe_name: '',
        description: '',
        serving_size: 1,
        genre: 'dinner',
        prep_time: 0,
        cook_time: 0,
        dietary_restrictions: []
      });
      setIngredients([{ name: '', quantity: '', unit: 'cup' }]);
      setInstructions(['']);
      setNotes(['']);
      setPhotoFile(null);
      setPhotoPreview(null);
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
    console.log('Full error response:', error.response);

    // Log the exact validation error details from backend
    if (error.response?.data) {
      console.log('Backend error details:', error.response.data);
    }

    // IMPROVED: Better error handling with specific validation messages
    if (error.message && error.message.includes('Invalid quantity')) {
      // This is our custom validation error
      setError(error.message);
    } else if (error.response?.data?.detail) {
      // Backend validation error - show the specific details
      let errorMessage = error.response.data.detail;

      // If it's an array of validation errors, format them nicely
      if (Array.isArray(errorMessage)) {
        const formattedErrors = errorMessage.map(err => {
          if (err.loc && err.msg) {
            const field = err.loc.join(' -> ');
            return `${field}: ${err.msg}`;
          }
          return err.msg || err;
        });
        errorMessage = formattedErrors.join('; ');
      }

      setError(`Validation error: ${errorMessage}`);
    } else if (error.response?.status === 422) {
      setError('Recipe validation failed. Please check the browser console for details and verify all fields are correctly filled.');
    } else if (error.response?.status === 400) {
      setError('Invalid recipe data. Please check your inputs and try again.');
    } else if (error.response?.status === 413) {
      setError('Recipe data or photo is too large. Please reduce the size and try again.');
    } else if (error.message.includes('Network Error')) {
      setError('Network error. Please check your connection and try again.');
    } else {
      setError('Failed to save recipe. Please try again.');
    }
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

  const dietaryBadgeStyle = (selected) => ({
    display: 'inline-block',
    padding: '8px 12px',
    margin: '0 8px 8px 0',
    borderRadius: '20px',
    fontSize: '0.9rem',
    cursor: 'pointer',
    backgroundColor: selected ? '#28a745' : '#f0f8ff',
    color: selected ? 'white' : '#666',
    border: `2px solid ${selected ? '#28a745' : '#ccc'}`,
    transition: 'all 0.2s ease'
  });

  // Render guard
  if (!isAuthenticated()) {
    return null;
  }

  // Show loading state for temp recipe
  if (isLoadingTempRecipe) {
    return (
      <div style={containerStyle}>
        <div style={formContainerStyle}>
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            padding: '3rem',
            textAlign: 'center'
          }}>
            <div style={{
              width: '50px',
              height: '50px',
              border: '4px solid #f0f8ff',
              borderTop: '4px solid #003366',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              marginBottom: '1rem'
            }}></div>
            <h2 style={{ color: '#003366', marginBottom: '1rem' }}>
              ✨ Loading Recipe from Ralph...
            </h2>
            <p style={{ color: '#666' }}>
              Preparing your recipe data for the form! 🍳
            </p>
          </div>
        </div>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
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

          {/* Description */}
          <div style={{ marginBottom: '2rem' }}>
            <label style={labelStyle}>Description (Optional)</label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              style={{
                ...inputStyle,
                minHeight: '100px',
                resize: 'vertical'
              }}
              placeholder="Brief description of your recipe (e.g., 'A delicious chocolate chip cookie recipe passed down from my grandmother...')"
              maxLength={500}
            />
            <div style={{
              fontSize: '12px',
              color: formData.description.length > 450 ? '#dc3545' : '#666',
              marginTop: '0.5rem',
              textAlign: 'right'
            }}>
              {formData.description.length}/500 characters
            </div>
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

          {/* Dietary Restrictions Section */}
          <div style={{ marginBottom: '2rem' }}>
            <label style={labelStyle}>Dietary Restrictions (Optional)</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
              {availableDietaryRestrictions.map(restriction => (
                <button
                  key={restriction}
                  type="button"
                  onClick={() => handleDietaryRestrictionChange(restriction)}
                  style={dietaryBadgeStyle(formData.dietary_restrictions.includes(restriction))}
                >
                  {formatDietaryRestrictionName(restriction)}
                </button>
              ))}
            </div>
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

          {/* Photo Upload Section */}
          <div style={{ marginBottom: '2rem' }}>
            <label style={labelStyle}>Recipe Photo (Optional)</label>

            {/* Photo Preview */}
            {photoPreview && (
              <div style={{
                marginBottom: '1rem',
                padding: '1rem',
                border: '2px solid #003366',
                borderRadius: '10px',
                backgroundColor: '#f8f9fa'
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  marginBottom: '0.5rem'
                }}>
                  <span style={{ fontWeight: '500', color: '#003366' }}>📸 Recipe Photo Preview</span>
                  <button
                    type="button"
                    onClick={removePhoto}
                    style={{
                      ...removeButtonStyle,
                      padding: '4px 8px',
                      fontSize: '12px'
                    }}
                  >
                    ✕ Remove
                  </button>
                </div>
                <img
                  src={photoPreview}
                  alt="Recipe preview"
                  style={{
                    width: '100%',
                    maxWidth: '300px',
                    height: 'auto',
                    borderRadius: '8px',
                    border: '1px solid #ddd'
                  }}
                />
              </div>
            )}

            {/* Camera Error */}
            {cameraError && (
              <div style={{
                background: '#f8d7da',
                color: '#721c24',
                padding: '0.75rem',
                borderRadius: '8px',
                marginBottom: '1rem',
                border: '1px solid #f5c6cb',
                fontSize: '0.9rem'
              }}>
                {cameraError}
              </div>
            )}

            {/* Camera Interface */}
            {showCamera && (
              <div style={{
                marginBottom: '1rem',
                padding: '1rem',
                border: '2px solid #003366',
                borderRadius: '10px',
                backgroundColor: '#f8f9fa'
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '1rem'
                }}>
                  <span style={{ fontWeight: '500', color: '#003366' }}>📷 Camera Active</span>
                  <button
                    type="button"
                    onClick={stopCamera}
                    style={{
                      ...removeButtonStyle,
                      padding: '4px 8px',
                      fontSize: '12px'
                    }}
                  >
                    ✕ Close
                  </button>
                </div>

                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  style={{
                    width: '100%',
                    maxWidth: '400px',
                    height: 'auto',
                    borderRadius: '8px',
                    border: '1px solid #ddd',
                    marginBottom: '1rem'
                  }}
                />

                <div style={{ textAlign: 'center' }}>
                  <button
                    type="button"
                    onClick={capturePhoto}
                    style={{
                      ...addButtonStyle,
                      backgroundColor: '#007bff',
                      fontSize: '16px',
                      padding: '12px 24px'
                    }}
                  >
                    📸 Take Photo
                  </button>
                </div>
              </div>
            )}

            {/* Upload Options */}
            {!showCamera && (
              <div style={{
                display: 'flex',
                gap: '1rem',
                flexWrap: 'wrap'
              }}>
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  style={{
                    ...addButtonStyle,
                    backgroundColor: '#17a2b8',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem'
                  }}
                >
                  📁 Choose from File
                </button>

                <button
                  type="button"
                  onClick={startCamera}
                  style={{
                    ...addButtonStyle,
                    backgroundColor: '#007bff',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem'
                  }}
                >
                  📷 Take Photo
                </button>
              </div>
            )}

            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />

            {/* Hidden canvas for photo capture */}
            <canvas
              ref={canvasRef}
              style={{ display: 'none' }}
            />

            <div style={{
              fontSize: '0.8rem',
              color: '#666',
              marginTop: '0.5rem',
              fontStyle: 'italic'
            }}>
              💡 Add a photo to make your recipe more appealing! Supports JPG, PNG, and other image formats.
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