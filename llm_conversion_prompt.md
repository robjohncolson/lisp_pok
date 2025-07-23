# AP Statistics Quiz to JSON Conversion Task

You are tasked with converting AP Statistics quiz questions from uploaded PDF documents into a specific JSON format. Each question should be converted to a separate JSON object following this structure:

## JSON Format Template:

### For Multiple Choice Questions:
```json
{
  "id": "U#-L#-Q##",  // Use appropriate ID format based on quiz type (see ID Format section)
  "type": "multiple-choice",
  "prompt": "Question text here",
  "attachments": {
    // Include visual data if present:
    
    // For images/diagrams:
    "image": "assets/pngs/unit3/u3_l3_q1.png",
    "imageAlt": "Map of the study region showing three distinct areas: a town with grid pattern buildings, a forest with trees, and a lake with irregular shoreline",
    "imageCaption": "Study region diagram showing the town, forest, and lake areas where salt licks will be placed"
    
    // For multiple images:
    "images": [
      {
        "image": "assets/pngs/unit3/u3_l3_q1a.png",
        "imageAlt": "First diagram description",
        "imageCaption": "Caption for first diagram"
      },
      {
        "image": "assets/pngs/unit3/u3_l3_q1b.png", 
        "imageAlt": "Second diagram description",
        "imageCaption": "Caption for second diagram"
      }
    ]
    
    // For tables:
    "table": [["Header1","Header2"],["data1","data2"],...]
    
    // For bar charts (categorical data with gaps between bars):
    "chartType": "bar",
    "xLabels": ["Category1", "Category2", ...],
    "series": [
      {"name": "Dataset 1", "values": [0.1, 0.2, 0.3, ...]},
      {"name": "Dataset 2", "values": [0.15, 0.25, 0.35, ...]}
    ],
    "chartConfig": {
      "yAxis": {
        "min": 0,           // Minimum value on y-axis
        "max": 1.0,         // Maximum value on y-axis (if specified)
        "tickInterval": 0.25, // Step size between tick marks (e.g., 0.1, 0.25, 0.5)
        "title": "Relative Frequency" // Y-axis label
      },
      "xAxis": {
        "title": "Grade"    // X-axis label
      },
      "gridLines": {
        "horizontal": true,  // Whether horizontal grid lines are shown
        "vertical": false    // Whether vertical grid lines are shown
      },
      "description": "Bar chart showing relative frequency by grade level with gaps between bars"
    }
    
    // For STACKED bar charts (segmented bars showing parts of a whole):
    "chartType": "bar",
    "xLabels": ["Ninth", "Tenth", "Eleventh", "Twelfth"],
    "series": [
      {"name": "Yes", "values": [0.6, 0.75, 0.75, 0.5]},
      {"name": "No", "values": [0.4, 0.25, 0.25, 0.5]}
    ],
    "chartConfig": {
      "stacked": true,      // CRITICAL: Enable stacking for segmented bars
      "yAxis": {
        "min": 0,
        "max": 1.0,
        "tickInterval": 0.2,
        "title": "Relative Frequency"
      },
      "xAxis": {
        "title": "Grade Level"
      },
      "gridLines": {
        "horizontal": true,
        "vertical": false
      },
      "description": "Stacked bar chart showing relative frequency of yes/no responses by grade level"
    }
    
    // For horizontal bar charts (bars extend horizontally):
    "chartType": "bar",
    "yLabels": ["Category1", "Category2", ...],  // Categories on y-axis - ORDERING CRITICAL!
    "series": [
      {"name": "Dataset 1", "values": [25, 30, 55, 15, 5]},
      {"name": "Dataset 2", "values": [35, 20, 40, 25, 16]}
    ],
    "chartConfig": {
      "orientation": "horizontal",  // Specifies horizontal orientation
      "xAxis": {
        "min": 0,           // Minimum value on x-axis (value axis)
        "max": 60,          // Maximum value on x-axis (if specified)
        "tickInterval": 10, // Step size between tick marks
        "title": "Number of Students" // X-axis label (value axis)
      },
      "yAxis": {
        "title": "School Subject"    // Y-axis label (category axis)
      },
      "gridLines": {
        "horizontal": true,  // Whether horizontal grid lines are shown
        "vertical": false    // Whether vertical grid lines are shown
      },
      "description": "Horizontal bar chart showing favorite school subjects by grade level"
    }
    
    // For STACKED horizontal bar charts (segmented horizontal bars):
    "chartType": "bar",
    "yLabels": ["Airport R", "Airport S", "Airport T"],
    "series": [
      {"name": "On time", "values": [100, 100, 200]},
      {"name": "Delayed", "values": [50, 100, 300]}
    ],
    "chartConfig": {
      "orientation": "horizontal",  // Horizontal orientation
      "stacked": true,             // CRITICAL: Enable stacking for segmented bars
      "xAxis": {
        "min": 0,
        "max": 600,
        "tickInterval": 200,
        "title": "Number of Flights"
      },
      "yAxis": {
        "title": "Airport"
      },
      "gridLines": {
        "horizontal": true,
        "vertical": false
      },
      "description": "Segmented bar chart showing on-time and delayed flights by airport with stacked bars"
    }
    
    // ⚠️ CRITICAL ORDERING REQUIREMENTS FOR HORIZONTAL BAR CHARTS:
    // 1. yLabels array order determines visual ordering from TOP to BOTTOM
    // 2. series array order determines which dataset appears in FRONT (first = front/left)
    // 3. values arrays must match the yLabels order exactly
    // 4. Always match the EXACT ordering shown in the reference image!
    
    // For histograms (continuous data with NO gaps between bars):
    "chartType": "histogram",
    "xLabels": ["0-10", "10-20", "20-30", ...],  // Use ranges if PDF shows "0-10, 10-20, 20-30"
    "series": [
      {"name": "Frequency", "values": [5, 12, 8, 3, ...]},
    ],
    "chartConfig": {
      "yAxis": {
        "min": 0,
        "max": 15,
        "tickInterval": 5,
        "title": "Frequency"
      },
      "xAxis": {
        "title": "Score Range",
        "labelType": "range"  // Use "range" when PDF shows "0-10, 10-20, 20-30"
      },
      "gridLines": {
        "horizontal": false,  // CAREFULLY observe - many histograms have NO grid lines
        "vertical": false
      },
      "description": "Histogram showing score distribution with no gaps between bars"
    }
    
    // Alternative histogram format (when PDF shows upper bounds like "200, 400, 600"):
    "chartType": "histogram",
    "xLabels": ["200", "400", "600", "800", "1000", "1200"],  // Single values when PDF shows upper bounds
    "series": [
      {"name": "Number of Students", "values": [4, 6, 9, 7, 3, 1]},
    ],
    "chartConfig": {
      "yAxis": {
        "min": 0,
        "max": 10,
        "tickInterval": 1,
        "title": "Number of Students"
      },
      "xAxis": {
        "title": "Amount Spent (Dollars)",
        "labelType": "upperBound",  // Use "upperBound" when PDF shows single values like "200, 400, 600"
        "labels": [200, 400, 600, 800, 1000, 1200]  // Numeric values for precise labeling
      },
      "gridLines": {
        "horizontal": false,  // CAREFULLY observe - many histograms have NO grid lines
        "vertical": false
      },
      "description": "Histogram showing spending distribution with upper bound labels"
    }
    
    // For pie charts:
    "chartType": "pie",
    "series": [
      {
        "name": "Category Distribution",
        "values": [
          {"name": "Weather", "value": 70},
          {"name": "Overbooking", "value": 15},
          {"name": "Other", "value": 8}
        ]
      }
    ],
    "chartConfig": {
      "showPercentages": true,  // Whether percentages are displayed
      "showValues": true,       // Whether raw values are shown
      "description": "Pie chart showing flight delay reasons with percentages"
    }
    
    // For scatter plots:
    "chartType": "scatter",
    "points": [{"x": 1.2, "y": 3.4, "label": "A"}, {"x": 2.1, "y": 4.7, "label": "B"}, ...],
    "chartConfig": {
      "xAxis": {
        "min": 0, "max": 10, "tickInterval": 1, "title": "X Variable"
      },
      "yAxis": {
        "min": 0, "max": 10, "tickInterval": 2, "title": "Y Variable"
      },
      "gridLines": {
        "horizontal": true,
        "vertical": true
      },
      "referenceLineAtZero": true,  // NEW: draw a dashed reference line at y = 0 (useful for residual plots)
      "regressionLine": true,       // NEW: include least-squares regression line (auto-computed)
      "regressionLineColor": "#000000", // OPTIONAL: override line color (defaults adapt to theme)
      "regressionLineDash": [4, 2],      // OPTIONAL: dash pattern (Chart.js format)
      "showPointLabels": true,           // OPTIONAL: by default, any point object that includes a "label" field (e.g., {"x": 53, "y": 6100, "label": "A"}) will be rendered with that label on the chart.  Set "showPointLabels": true to force EVERY point to display a label (points without an explicit "label" will fall back to their coordinates).
      "description": "Scatter plot with axis ranges, tick intervals, an optional y=0 reference line, and an auto-generated least-squares regression line"
    }
    
    // For dotplots (for single or comparative distributions):
    "chartType": "dotplot",
    "values": [55, 60, 60, 60, 60, 65, 65, 65, 70, 70, 70, 75, 75, 80, 85, 90, 95],
    "chartConfig": {
      "xAxis": {
        "min": 50, "max": 100, "tickInterval": 5, "title": "Score"
      },
      "gridLines": {
        "horizontal": false,
        "vertical": false
      },
      "description": "Dotplot showing distribution of scores with dots stacked vertically"
    }
    
    // For boxplots (five-number summary visualization):
    "chartType": "boxplot",
    "chartConfig": {
      "orientation": "horizontal",  // "horizontal" or "vertical" - controls boxplot orientation
      "xAxis": {
        "min": 28, "max": 44, "tickInterval": 2, "title": "Tree Height (inches)"
      },
      "boxplotData": {
        "Q1": 32,
        "Q3": 38,
        "median": 35,
        "whiskerMin": 30,  // End of lower whisker (most extreme non-outlier value)
        "whiskerMax": 42,  // End of upper whisker (most extreme non-outlier value)
        "outliers": []     // Array of outlier values (empty if no outliers)
      },
      "gridLines": {
        "horizontal": false,
        "vertical": false
      },
      "description": "Boxplot showing the heights of a sample of 100 trees growing on a tree farm"
    }
    
    // For MULTIPLE boxplots in the same chart (comparative boxplots):
    "chartType": "boxplot",
    "chartConfig": {
      "orientation": "horizontal",  // "horizontal" or "vertical" - controls boxplot orientation
      "xAxis": {
        "min": 0, "max": 12.5, "tickInterval": 2.5, "title": "ERA"
      },
      "boxplotData": [
        {
          "name": "League A",
          "Q1": 2.5,
          "Q3": 5.0,
          "median": 3.5,
          "whiskerMin": 1.5,     // End of lower whisker
          "whiskerMax": 7.5,     // End of upper whisker
          "outliers": [0.8, 10.2]  // Explicit outlier values (if any)
        },
        {
          "name": "League B",
          "Q1": 2.5,
          "Q3": 5.0,
          "median": 4.0,
          "whiskerMin": 1.2,     // End of lower whisker
          "whiskerMax": 8.5,     // End of upper whisker
          "outliers": [0.4, 12.0]  // Explicit outlier values (if any)
        }
      ],
      "gridLines": {
        "horizontal": false,
        "vertical": false
      },
      "description": "Boxplots comparing ERA for pitchers in leagues A and B, showing outliers marked with asterisks"
    }
    
    // For normal distribution curves (bell curves):
    "chartType": "normal",
    "mean": 0,              // Mean (µ) of the normal distribution
    "sd": 5.9,              // Standard deviation (σ)
    "shade": {              // OPTIONAL: shaded region under the curve
      "lower": 8,           // Lower bound of shading (null if none)
      "upper": null         // Upper bound of shading (null ⇒ extend to +∞).  Provide both bounds to shade an interval.
    },
    "chartConfig": {
      "xAxis": {
        "min": -17.7,       // Typically µ − 3σ (override as needed)
        "max": 17.7,        // Typically µ + 3σ
        "tickInterval": 5.9,
        "title": "Residual (cm)"
      },
      "yAxis": {
        "title": "Density"  // Density axis – renderer hides it by default
      },
      "gridLines": {
        "horizontal": false,
        "vertical": false
      },
      "description": "Normal distribution curve with right-tail shaded to represent P(residual > 8 cm)"
    }
    
    // NEW ➜ For chi-square distribution curves (right-skewed gamma family):
    "chartType": "chisquare",
    "dfList": [1, 3, 6, 10, 20],   // Degrees of freedom for each curve (order matters)
    "labels": ["A", "B", "C", "D", "E"],  // Optional legend/series labels; default "df = k"
    "overlay": true,               // true → render ALL curves in one chart (default); false → supply separate charts
    "chartConfig": {
      "xAxis": { "min": 0, "max": 35, "tickInterval": 5, "title": "χ²" },
      "yAxis": { "title": "Density" },        // Usually implicit; include if PDF shows it
      "gridLines": { "horizontal": false, "vertical": false },
      "description": "Five chi-square curves with increasing degrees of freedom – skew diminishes as df grows"
    }
    
    // Notes:
    //  • Omitting dfList and giving a single "df" (number) also works for one curve.
    //  • The renderer computes the chi-square PDF dynamically via a gamma-function approximation.
    //  • Provide at least x-axis limits so the curves match the PDF image's window.
    //  • Use labels when the PDF calls curves A-E, etc.; otherwise they default to "df = 4", etc.
    
    // For number line diagrams (interval ticks along a single axis):
    "chartType": "numberline",
    "ticks": [
      { "x": -2.5, "label": "a", "drawTick": false },     // segment label (no tick)
      { "x": -2,   "bottomLabel": "\u0305x-2s" },          // tick with value label below line
      { "x": -1.5, "label": "b", "drawTick": false },
      { "x": -1,   "bottomLabel": "\u0305x-s" },
      { "x":  0,   "label": "c", "drawTick": false },      // middle segment label
      { "x":  1,   "bottomLabel": "\u0305x+s" },
      { "x":  1.5, "label": "d", "drawTick": false },
      { "x":  2,   "bottomLabel": "\u0305x+2s" },
      { "x":  2.5, "label": "e", "drawTick": false }
    ],
    //  • "label" / "topLabel": text above the baseline
    //  • "bottomLabel" / "valueLabel": text below the baseline (e.g., \u0305x ± ks)
    //  • "drawTick": false —> suppresses the vertical tick mark at that x
    "xAxis": { "min": -3, "max": 3 },
    "chartConfig": { "description": "Number line with segment labels above and tick value labels below" }
    
    "choices": [
      { "key": "A", "value": "Choice A text" },
      { "key": "B", "value": "Choice B text" },
      { "key": "C", "value": "Choice C text" },
      { "key": "D", "value": "Choice D text" },
      { "key": "E", "value": "Choice E text" }
    ]
  },
  "answerKey": "B",
  "reasoning": "Detailed explanation of why the correct answer is correct. This should include the mathematical reasoning, conceptual understanding, or step-by-step solution process that leads to the correct answer. Extract this information from the answer key, scoring guide, or solution manual provided with the quiz."
}
```

### For Free Response Questions:
```json
{
  "id": "U#-L#-Q##",  // Use appropriate ID format based on quiz type (see ID Format section)
  "type": "free-response",
  "prompt": "Question text here, including all sub-parts (a), (b), (c), etc.",
  "attachments": {
    // Include visual data from the QUESTION itself (tables, charts, etc.)
    "table": [["Header1","Header2"],["data1","data2"],...]
    // Use same chart formats as above for question visuals
  },
  "solution": {
    "parts": [
      {
        "partId": "a-i",
        "description": "Use the data in the table to create a histogram showing the distribution of the amounts of the orders.",
        "response": "Complete solution explanation for this part.",
        "attachments": {
          // Include visual data from the SOLUTION (charts, graphs, images created as part of the answer)
          
          // For solution images/diagrams:
          "image": "assets/pngs/unit3/u3_l3_q1_solution.png",
          "imageAlt": "Solution diagram showing the completed histogram",
          "imageCaption": "Histogram created from the data table showing distribution of order amounts"
          
          // For solution charts:
          "chartType": "histogram",
          "xLabels": ["0-5", "5-10", "10-15", "15-20", "20-25", "25-30"],
          "series": [
            {"name": "Frequency", "values": [8, 14, 25, 27, 12, 5]}
          ],
          "chartConfig": {
            "yAxis": {"min": 0, "max": 30, "tickInterval": 5, "title": "Frequency"},
            "xAxis": {"title": "Amounts (in dollars)", "labelType": "range"},
            "gridLines": {"horizontal": true, "vertical": false},
            "description": "Histogram showing distribution of order amounts"
          }
        }
      },
      {
        "partId": "a-ii",
        "description": "Describe the shape of the distribution of amounts.",
        "response": "The distribution of the amounts of the orders appears to be roughly symmetric and mound shaped or approximately normal."
      },
      {
        "partId": "b",
        "description": "Identify a possible amount for the median of the distribution. Justify your answer.",
        "response": "The median could be any value from $10 up to but not including $15. In a distribution of 91 values, the median value is the 46th value when all 91 values are ordered. The frequency of the first three bars sums to 47: 8 + 14 + 25 = 47. The 46th value corresponds to a value in the third bar of the histogram.",
        "calculations": [
          "Total values: 91",
          "Median position: (91+1)/2 = 46th value",
          "Cumulative frequency: 8 + 14 + 25 = 47",
          "46th value falls in the $10-$15 interval"
        ]
      }
    ],
    "scoring": {
      "totalPoints": 4,
      "rubric": [
        {
          "part": "a-i",
          "maxPoints": 2,
          "criteria": [
            "The histogram contains six bars with approximately correct heights of the bars",
            "The horizontal axis is labeled with correct numbers and a correct verbal description",
            "The vertical axis is labeled with correct numbers and a correct verbal description"
          ],
          "scoringNotes": "Essentially correct (E) if the response contains all components. Partially correct (P) if the response satisfies 3 of the 4 components. Incorrect (I) if the response does not satisfy the criteria for E or P."
        },
        {
          "part": "a-ii",
          "maxPoints": 1,
          "criteria": [
            "The shape of the distribution is described as roughly symmetric and mound shaped or approximately normal"
          ]
        },
        {
          "part": "b",
          "maxPoints": 1,
          "criteria": [
            "Response correctly identifies a value for the median that is contained within the interval from $10 up to but not including $15 AND provides a reasonable justification for how the median was determined"
          ],
          "scoringNotes": "Essentially correct (E) if both criteria met. Partially correct (P) if identifies correct interval BUT provides weak justification. Incorrect (I) if response does not satisfy criteria for E or P."
        }
      ]
    }
  },
  "reasoning": "Overall explanation of the solution approach and key statistical concepts being tested."
}
```

## Key Requirements:
1. **Image Handling**: When questions include diagrams, maps, or other visual elements:
   - Screenshots will be stored in `assets/pngs/unit#/` directory
   - Files are named using pattern: `u{unit}_{lesson}_q{question}.png` (e.g., `u3_l3_q1.png`)
   - Include the image reference in attachments with descriptive alt text and optional caption
   - Remove redundant text from prompt that refers to "the diagram below" or similar
   - For solution images, use similar naming with `_solution` suffix if needed
   - Multiple images can be included using the `images` array format
2. **ID Format**: Use appropriate pattern based on quiz type:
   - **Regular Lessons**: "U#-L#-Q##" (e.g., "U1-L2-Q05" for Unit 1, Lesson 2, Question 5)
   - **Progress Check MCQ**: "U#-PC-MCQ-[PART]-Q##" (e.g., "U1-PC-MCQ-A-Q01" for Unit 1, Progress Check, MCQ Part A, Question 1)
   - **Progress Check FRQ**: "U#-PC-FRQ-Q##" (e.g., "U1-PC-FRQ-Q01" for Unit 1, Progress Check, FRQ Question 1)
   - **AP Exam Questions**: "U#-AP-[YEAR]-[TYPE]-Q##" (e.g., "U1-AP-2017-MCQ-Q09" for Unit 1, AP 2017, MCQ Question 9)
   - **Other Quiz Types**: Adapt pattern to reflect the actual quiz type and source
3. **Visual Data**: Extract and format any tables, charts, graphs, or images according to the specifications above
4. **Clean Prompts**: Remove table formatting from prompt text when table data is included in attachments; remove references to "diagram below" when image is included
5. **Answer Keys**: Include the correct answer from the scoring guide
6. **Reasoning**: Extract the explanation for why the answer is correct from the answer key, scoring guide, or solution manual
7. **Complete Output**: Provide all questions as separate JSON objects in a single code artifact
8. **LaTeX Math Notation**: Wrap every mathematical expression in LaTeX delimiters (\\( ... \\) for inline or \\[ ... \\] for display) and use commands like \\hat{}, \\bar{}, \\sigma, etc., so MathJax in the renderer displays the notation correctly.

## Critical Chart Type Identification:

### Bar Charts vs. Histograms - This Distinction is Essential for AP Statistics!

**Bar Charts (for categorical data):**
- **Visual cues**: Clear gaps/spaces between bars
- **Orientation**: Can be vertical (bars extend upward) or horizontal (bars extend rightward)
- **Vertical Bar Charts**: Categories on x-axis, values on y-axis
  - **X-axis labels**: Discrete categories (e.g., "Freshman", "Sophomore", "Junior", "Senior")
  - **Use**: `"xLabels": [...categories...]` and standard axis configuration
- **Horizontal Bar Charts**: Categories on y-axis, values on x-axis
  - **Y-axis labels**: Discrete categories (e.g., "Language Arts", "Math", "Science")
  - **Use**: `"yLabels": [...categories...]` and `"orientation": "horizontal"` in chartConfig
- **Data type**: Categorical variables
- **Use chartType**: "bar"

**STACKED Bar Charts (segmented bars showing parts of a whole):**
- **Visual cues**: Bars are divided into colored segments that stack on top of each other
- **Purpose**: Show both the total and the composition (e.g., "Yes" and "No" responses stacked to show 100%)
- **Key identifier**: Multiple data series with bars that appear as segments within each category
- **Common in AP Stats**: Relative frequency charts, survey response breakdowns, conditional distributions
- **CRITICAL**: Must include `"stacked": true` in chartConfig
- **Example patterns**: 
  - Survey responses by grade level (Yes/No stacked to 100%)
  - Flight status by airport (On-time/Delayed stacked)
  - Gender breakdown by school year (Male/Female stacked)
- **Use chartType**: "bar" with `"stacked": true` in chartConfig

**Histograms (for continuous data):**
- **Visual cues**: NO gaps between bars - bars touch each other
- **X-axis labels**: Can be either:
  - **Ranges**: "0-10", "10-20", "20-30" (use `labelType: "range"`)
  - **Upper bounds**: "200", "400", "600" (use `labelType: "upperBound"`)
  - **Lower bounds**: "0, 10, 20" (use `labelType: "lowerBound"`)
- **Grid lines**: Often NO grid lines - observe carefully!
- **Data type**: Continuous/quantitative variables
- **Use chartType**: "histogram"

**Scatter Plots (for two variable relationships):**
- **Visual cues**: Dots scattered across both dimensions
- **X-axis**: One quantitative variable
- **Y-axis**: Another quantitative variable with explicit labels
- **Data type**: Two quantitative variables showing relationship
- **Use chartType**: "scatter"

**Boxplots (for five-number summary visualization):**
- **Visual cues**: Rectangular box with whiskers extending from both ends
- **Components**: Box (Q1 to Q3), median line inside box, whiskers (to min/max or fences), possible outlier points
- **Purpose**: Shows distribution shape, spread, and identifies outliers
- **Data needed**: Five-number summary PLUS explicit outlier handling
- **Orientation**: 
  - **Horizontal**: Box extends left-right, values on x-axis (use `"orientation": "horizontal"`)
  - **Vertical**: Box extends up-down, values on y-axis (use `"orientation": "vertical"`)
- **Multiple boxplots**: When comparing groups, use an array of boxplot objects in `boxplotData`
- **CRITICAL - Outlier Handling**: 
  - **whiskerMin/whiskerMax**: These are the endpoints of the whiskers (most extreme NON-outlier values)
  - **outliers**: Array of explicit outlier values that appear as separate points (asterisks/dots)
  - **DO NOT use min/max** - this is ambiguous about whether extreme values are outliers or whisker endpoints
  - **Visual identification**: Look for asterisks (*) or dots beyond the whiskers - these are outliers
  - **Fidelity**: This approach ensures exact match to reference images rather than auto-calculated outliers
- **Use chartType**: "boxplot"

**Chi-Square Distribution Curves (continuous, right-skewed):**
- **Visual cues**: Starts at x = 0 with vertical line, peaks quickly, long right tail; skew decreases as degrees of freedom (df) increase.
- **JSON representation**: `chartType: "chisquare"` with `dfList` (or single `df`) to generate one or more curves.
- **Usage**: Comparing multiple chi-square PDFs (e.g., "Which curve has smallest df?" questions).
- **Axes**: x-axis positive only; y-axis density often unlabeled; no grid lines by default.
- **Stacking/overlay**: Use `overlay: true` for one combined chart; otherwise supply separate charts via `charts` array.

## Multiple Charts Strategy:

**Overlaid Histograms (same chart, different colors):**
- Use when comparing distributions side-by-side
- Both distributions use the same x-axis scale
- Good for showing relative differences
- Use multiple series in the same histogram JSON

**Separate Histograms (different charts):**
- Use when distributions have very different scales
- When the question explicitly shows them as separate charts
- Use the `charts` array structure within attachments
- Each histogram gets its own chart space and title

Example of separate histograms:
```json
"attachments": {
  "charts": [
    {
      "chartType": "histogram",
      "title": "Earthquake Disturbances",
      "xLabels": ["0.2", "0.4", "0.6", "0.8"],
      "series": [
        {"name": "Earthquake Disturbances", "values": [0.35, 0.20, 0.10, 0.10]}
      ],
      "chartConfig": {
        "yAxis": {"min": 0.0, "max": 0.40, "tickInterval": 0.05, "title": "Relative Frequency"},
        "xAxis": {"title": "Root Mean Square Time", "labelType": "upperBound"},
        "gridLines": {"horizontal": true, "vertical": false}
      }
    },
    {
      "chartType": "histogram", 
      "title": "Mining Disturbances",
      "xLabels": ["0.2", "0.4", "0.6", "0.8"],
      "series": [
        {"name": "Mining Disturbances", "values": [0.0, 0.22, 0.35, 0.25]}
      ],
      "chartConfig": {
        "yAxis": {"min": 0.0, "max": 0.40, "tickInterval": 0.05, "title": "Relative Frequency"},
        "xAxis": {"title": "Root Mean Square Time", "labelType": "upperBound"},
        "gridLines": {"horizontal": true, "vertical": false}
      }
    }
  ],
  "description": "Overall description of the multiple charts"
}
```

**Multiple Boxplots (same chart space):**
- Use when comparing groups (e.g., "League A vs League B")
- Put multiple boxplot objects in the `boxplotData` array
- Each boxplot gets its own name and color
- The renderer will space them appropriately

**Multiple Dotplots (same chart space):**
- Use when comparing two or more distributions of the same quantitative variable (e.g., first-time vs previously married couples)
- Provide a `"series"` array where each object has `"name"` and `"values"` keys
- All groups share the same x-axis scale; the renderer should automatically offset or color each group's dots to avoid overlap

Example:
```json
"attachments": {
  "chartType": "dotplot",
  "series": [
    { "name": "First Time", "values": [0.5, 10, 18, 20, 36] },
    { "name": "Previously Married", "values": [0.5, 8, 12, 16, 20] }
  ],
  "chartConfig": {
    "xAxis": { "min": 0, "max": 40, "tickInterval": 5, "title": "Time (months) Between Proposal and Wedding" },
    "gridLines": { "horizontal": false, "vertical": false },
    "description": "Overlaid dotplot comparing time between proposal and wedding for two marriage types"
  }
}
```

## Instructions:
- Analyze the uploaded PDF carefully
- **Identify quiz type from document headers/titles** - Look for indicators like "Progress Check," "AP Exam," "Lesson," "Section," "Capstone," "MCQ Part A/B," "FRQ," etc.
- **Apply appropriate ID format** based on quiz type identified (see ID Format section above)
- Identify unit and lesson numbers from document headers/titles
- **Extract visual elements** - Look for diagrams, maps, charts, graphs, or other visual content that needs to be preserved
- **Pay special attention to chart types** - look for gaps between bars to distinguish bar charts from histograms
- **Identify stacked/segmented bars** - look for bars divided into colored segments that show parts of a whole (common in relative frequency and survey data)
- **Check bar chart orientation** - determine if bars extend upward (vertical) or rightward (horizontal)
- **Look for stacked dots** - identify dotplots showing single variable distributions vs scatter plots showing two-variable relationships
- **Identify boxplots** - look for rectangular boxes with whiskers, median lines, and possible outlier points
- **Examine grid lines carefully** - note whether horizontal and/or vertical grid lines are present
- **Enable data labels when shown in the PDF** - If the reference image prints the numeric value directly on top of each bar (bar chart or histogram) or next to individual points (scatter plot or dotplot), add `"showPointLabels": true` inside the `chartConfig`. This triggers the renderer's built-in Chart.js DataLabels plugin so the values display exactly as they do in the PDF.
- **For stacked bar charts** - when bars show segmented data (like Yes/No responses or On-time/Delayed flights), add `"stacked": true` to chartConfig
- **For histograms, observe x-axis labels precisely**:
  - If PDF shows "0-10, 10-20, 20-30" → use range labels with `labelType: "range"`
  - If PDF shows "200, 400, 600" → use upper bound labels with `labelType: "upperBound"`
  - If PDF shows "0, 10, 20" → use lower bound labels with `labelType: "lowerBound"`
- **For boxplots, extract the five-number summary** - identify min, Q1, median, Q3, max values from the visual
- **Grid line detection is critical** - many AP Statistics charts have NO grid lines at all
- Convert each question following the exact format above
- Include all visual elements as structured data in attachments
- Preserve exact wording from the original questions
- Extract correct answers from the provided answer key/scoring guide
- **Extract reasoning for each answer** - Look for explanations in the answer key, scoring guide, or solution manual that explain WHY the correct answer is correct. Include the mathematical reasoning, conceptual understanding, statistical principles, or step-by-step solution process. This reasoning should be comprehensive enough to help students understand the solution approach.

### **Special Instructions for Free Response Questions:**
- **Capture complete solutions** - Free response questions often have detailed, multi-part solutions that include visual elements, step-by-step calculations, and comprehensive explanations
- **Extract solution visuals** - If the solution includes charts, graphs, or other visualizations (like sample histograms, boxplots, etc.), capture these in the solution's attachments using the same format as question visuals
- **Preserve part structure** - Maintain the exact part numbering (a-i, a-ii, b, c, etc.) from the original solution
- **Include scoring rubrics** - Extract the complete scoring criteria, point values, and scoring notes (E/P/I designations) from the scoring guide
- **Capture calculations** - If the solution shows mathematical work, include step-by-step calculations in the calculations array
- **Distinguish question vs solution visuals** - Question attachments go in the main attachments field, while solution visuals go in the solution.parts[].attachments field
- **Extract complete scoring criteria** - Include all requirements for "Essentially correct," "Partially correct," and "Incorrect" classifications
- **Preserve exact wording** - Maintain the precise language from scoring guides and solutions, as AP terminology is specific and important

Create a single code artifact containing all converted questions as separate JSON objects.

## Backward Compatibility Note:
- The old format `"gridLines": true` is still supported, but the new format `"gridLines": {"horizontal": true, "vertical": false}` is preferred for better precision.
- For histograms, the new `"labelType"` field enables precise x-axis labeling: use `"range"` for interval labels, `"upperBound"` for boundary labels, or `"lowerBound"` for lower bound labels.
- **Boxplots**: The old `"min"/"max"` format is deprecated. Use `"whiskerMin"/"whiskerMax"` + `"outliers"` array for precise outlier handling.

## Boxplot Outlier Identification Guide:
When converting boxplots from PDF images, follow these steps:

1. **Identify the box components**: 
   - Q1 (left/bottom edge of box)
   - Q3 (right/top edge of box) 
   - Median (line inside box)

2. **Locate whisker endpoints**:
   - Follow the whisker lines to their endpoints
   - These endpoints are `whiskerMin` and `whiskerMax`
   - These are NOT necessarily the true min/max of the dataset

3. **Identify outliers**:
   - Look for separate points (dots, asterisks *) beyond the whiskers
   - These isolated points are outliers
   - Extract their approximate values for the `outliers` array

4. **Avoid auto-calculation**:
   - Do NOT calculate outliers using IQR * 1.5 rule
   - Use only the visual information from the reference image
   - This ensures exact fidelity to the original visualization

**Example**: If you see a boxplot with whiskers ending at 8.5 and 1.2, but separate dots at 12.0 and 0.4, then:
- `whiskerMax: 8.5` (not 12.0)
- `whiskerMin: 1.2` (not 0.4)  
- `outliers: [0.4, 12.0]`


Finally, nomenclature of filenames are subject_unit#_lesson#_type, for example "ap_stats_u2_l5_quiz.json" is for ap stats, unit 2, lesson 5, quiz

**Image File Naming Convention:**
- Question images: `u{unit}_{lesson}_q{question}.png` (e.g., `u3_l3_q1.png`)
- Solution images: `u{unit}_{lesson}_q{question}_solution.png` (e.g., `u3_l3_q1_solution.png`)
- Multiple images for same question: `u{unit}_{lesson}_q{question}a.png`, `u{unit}_{lesson}_q{question}b.png`, etc.
- Images are stored in `assets/pngs/unit{unit}/` directory