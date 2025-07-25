
new Vue({
    el: '#app',
    data: {
        schema: null,
        sqlQuery: '',
        queryResult: null,
        displayedResults: null,
        queryError: null,
        loadingSchema: false,
        executing: false,
        showSchema: true,
        queryEditorHeight: 100,
        queryEditorExpanded: false,
        rowsPerPage: 50,
        currentPage: 1,
        showModal: false,
        modalData: null,
        rawModalData: null,
        modalColumnName: '',
        queryExamples: [
            { label: 'Select Sample', query: 'SELECT * FROM your_table LIMIT 10;' },
            { label: 'Count Rows', query: 'SELECT COUNT(*) FROM your_table;' },
            { label: 'List Tables', query: "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';" },
            { label: 'Table Columns', query: "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'your_table';" },
            { label: 'Database Size', query: "SELECT pg_size_pretty(pg_database_size(current_database()));" },
            { label: 'Active Connections', query: 'SELECT count(*) FROM pg_stat_activity;' }
        ],
        queryShortcut: [
            { label: 'Country', query: 'SELECT * FROM t_country;' },
            { label: 'Province', query: 'SELECT * FROM t_province;' },
            { label: 'City', query: 'SELECT * FROM t_city;' },
            { label: 'Postal Area', query: 'SELECT * FROM t_postal_area LIMIT 100;' },
            { label: 'Country, Province, City, Postal', query: `SELECT c_name, p_name, ci_name, pa_name, pa_code, pa_data 
FROM t_postal_area 
JOIN t_city ON t_city.ci_id = t_postal_area.ci_id 
JOIN t_province ON t_province.p_id = t_city.p_id
JOIN t_country ON t_country.c_id = t_province.c_id
LIMIT 100` },
            { label: 'Electricity data/hour', query: `SELECT pa_data->'energy'->'todayHours' AS "Electricity data/hour", pa_code "Zip Code", ci_name "City", c_name AS "Country"
FROM t_postal_area 
JOIN t_city ON t_city.ci_id = t_postal_area.ci_id 
JOIN t_province ON t_province.p_id = t_city.p_id
JOIN t_country ON t_country.c_id = t_province.c_id
WHERE c_name = 'Deutschland' AND pa_data IS NOT NULL
LIMIT 100;
` }
        ]
    },
    computed: {
        totalRows() {
            return this.queryResult ? this.queryResult.length : 0;
        },
        displayedRows() {
            return this.displayedResults ? this.displayedResults.length : 0;
        },
        hasMoreData() {
            return this.queryResult && this.displayedResults && 
                    this.displayedResults.length < this.queryResult.length;
        },
        remainingRows() {
            return this.totalRows - this.displayedRows;
        }
    },
    mounted() {
        this.loadSchema();
        // Add keyboard shortcut for query execution
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                this.executeQuery();
            }
            if (e.key === 'Escape' && this.showModal) {
                this.closeModal();
            }
        });
        
        // Handle window resize
        window.addEventListener('resize', this.handleResize);
        this.handleResize();
    },
    methods: {
        toggleSchema() {
            this.showSchema = !this.showSchema;
        },
        toggleQueryHeight() {
            this.queryEditorExpanded = !this.queryEditorExpanded;
            this.queryEditorHeight = this.queryEditorExpanded ? 200 : 100;
        },
        handleResize() {
            // Adjust query editor height based on screen size
            const vh = window.innerHeight;
            if (vh < 700) {
                this.queryEditorHeight = this.queryEditorExpanded ? 150 : 80;
            } else {
                this.queryEditorHeight = this.queryEditorExpanded ? 200 : 100;
            }
        },
        async loadSchema() {
            this.loadingSchema = true;
            try {
                const response = await fetch('/api/control/schema');
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                this.schema = data.data;
            } catch (error) {
                console.error('Error loading schema:', error);
                this.schema = 'Error loading schema: ' + error.message;
            } finally {
                this.loadingSchema = false;
            }
        },
        async executeQuery() {
            if (!this.sqlQuery.trim() || this.executing) return;
            
            this.executing = true;
            this.queryResult = null;
            this.displayedResults = null;
            this.queryError = null;
            this.currentPage = 1;
            
            try {
                const response = await fetch('/api/control/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        query: this.sqlQuery
                    })
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.detail || 'Query execution failed');
                }
                
                this.queryResult = data.data;
                this.loadInitialData();
            } catch (error) {
                console.error('Error executing query:', error);
                this.queryError = error.message;
            } finally {
                this.executing = false;
            }
        },
        loadInitialData() {
            if (this.queryResult && this.queryResult.length > 0) {
                this.displayedResults = this.queryResult.slice(0, this.rowsPerPage);
            } else {
                this.displayedResults = this.queryResult;
            }
        },
        loadMoreData() {
            if (!this.hasMoreData) return;
            
            const startIndex = this.displayedResults.length;
            const endIndex = Math.min(startIndex + this.rowsPerPage, this.queryResult.length);
            const newRows = this.queryResult.slice(startIndex, endIndex);
            
            this.displayedResults = [...this.displayedResults, ...newRows];
        },
        clearQuery() {
            this.sqlQuery = '';
            this.queryResult = null;
            this.displayedResults = null;
            this.queryError = null;
            this.currentPage = 1;
        },
        formatValue(value) {
            if (value === null || value === undefined) {
                return 'NULL';
            }
            if (typeof value === 'object') {
                return JSON.stringify(value);
            }
            const str = String(value);
            // Truncate very long values for display
            return str.length > 100 ? str.substring(0, 100) + '...' : str;
        },
        showCellData(data, columnName) {
            this.modalData = data;
            this.rawModalData = data === null || data === undefined ? 'NULL' : String(data);
            this.modalColumnName = columnName;
            this.showModal = true;
        },
        closeModal() {
            this.showModal = false;
            this.modalData = null;
            this.rawModalData = null;
            this.modalColumnName = '';
        },
        isJsonString(str) {
            if (typeof str !== 'string') return false;
            try {
                const parsed = JSON.parse(str);
                return typeof parsed === 'object' && parsed !== null;
            } catch (e) {
                return false;
            }
        },
        syntaxHighlight(json) {
            json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
                var cls = 'json-number';
                if (/^"/.test(match)) {
                    if (/:$/.test(match)) {
                        cls = 'json-key';
                    } else {
                        cls = 'json-string';
                    }
                } else if (/true|false/.test(match)) {
                    cls = 'json-boolean';
                } else if (/null/.test(match)) {
                    cls = 'json-null';
                }
                return '<span class="' + cls + '">' + match + '</span>';
            });
        },
        getDataType(data) {
            if (data === null || data === undefined) return 'NULL';
            if (this.isJsonString(data)) return 'JSON';
            return typeof data;
        },
        getDataLength(data) {
            if (data === null || data === undefined) return '0';
            return String(data).length;
        },
        async copyToClipboard(text) {
            if (typeof text === 'object' && text !== null) {
                text = JSON.stringify(text, null, 2);
            }
            try {
                await navigator.clipboard.writeText(text);
            } catch (err) {
                console.error('Failed to copy text: ', err);
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
            }
        }
    }
});