document.addEventListener('DOMContentLoaded', function () {
    // --- DOM ELEMENTEN ---
    const form = document.getElementById('ai-audit-form');
    const resultsSection = document.getElementById('results-section');
    const recommendationText = document.getElementById('recommendation-text');
    
    // Sliders en hun waarde-displays
    const sliders = {
        desire: { input: document.getElementById('desire-slider'), value: document.getElementById('desire-value') },
        capability: { input: document.getElementById('capability-slider'), value: document.getElementById('capability-value') },
        enjoyment: { input: document.getElementById('enjoyment-slider'), value: document.getElementById('enjoyment-value') },
        expertise: { input: document.getElementById('expertise-slider'), value: document.getElementById('expertise-value') },
        communication: { input: document.getElementById('communication-slider'), value: document.getElementById('communication-value') }
    };

    // --- CHART SETUP ---
    let desireCapabilityChart, humanAgencyChart, skillShiftChart;

    function createCharts() {
        // Grafiek 1: Desire vs Capability (Interactief)
        const dcCtx = document.getElementById('desireCapabilityChart').getContext('2d');
        desireCapabilityChart = new Chart(dcCtx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Uw Taak',
                    data: [], // Start leeg, wordt gevuld door gebruiker
                    backgroundColor: 'rgba(255, 99, 132, 1)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    pointRadius: 10,
                    pointHoverRadius: 15
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: { display: true, text: 'Technologische Capaciteit (%)' },
                        min: 0,
                        max: 100
                    },
                    y: {
                        title: { display: true, text: 'Wens tot Automatisering (%)' },
                        min: 0,
                        max: 100
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Capaciteit: ${context.parsed.x}%, Wens: ${context.parsed.y}%`;
                            }
                        }
                    }
                }
            }
        });

        // Grafiek 2: Human Agency Scale (Statisch)
        const haCtx = document.getElementById('humanAgencyChart').getContext('2d');
        humanAgencyChart = new Chart(haCtx, {
            type: 'line',
            data: {
                labels: ['H1', 'H2', 'H3', 'H4', 'H5 (Volledige Controle)'],
                datasets: [{
                    label: 'Wens van Werknemer',
                    data: [80, 75, 60, 40, 20],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }, {
                    label: 'Inschatting AI Expert',
                    data: [90, 85, 70, 65, 50],
                    borderColor: 'rgb(153, 102, 255)',
                    tension: 0.1
                }]
            },
            options: { responsive: true }
        });

        // Grafiek 3: Skill Shift (Statisch)
        const ssCtx = document.getElementById('skillShiftChart').getContext('2d');
        skillShiftChart = new Chart(ssCtx, {
            type: 'line',
            data: {
                labels: ['Lage AI Assistentie', 'Gemiddeld', 'Hoge AI Assistentie'],
                datasets: [
                    { label: 'Informatie Analyseren', data: [60, 80, 95], borderColor: 'rgb(54, 162, 235)', tension: 0.3 },
                    { label: 'Informatie Documenteren', data: [85, 40, 15], borderColor: 'rgb(255, 99, 132)', tension: 0.3 },
                    { label: 'Anderen Trainen/Onderwijzen', data: [40, 65, 80], borderColor: 'rgb(255, 206, 86)', tension: 0.3 }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: { title: { display: true, text: 'Belangrijkheid' } },
                    x: { title: { display: true, text: 'Mate van Menselijke Controle' } }
                }
            }
        });
    }

    // --- EVENT LISTENERS ---
    // Update slider waardes live
    Object.values(sliders).forEach(slider => {
        slider.input.addEventListener('input', () => {
            slider.value.textContent = slider.input.value;
        });
    });

    // Formulier indienen
    form.addEventListener('submit', function (e) {
        e.preventDefault();
        analyzeTask();
    });

    // --- FUNCTIES ---
    function analyzeTask() {
        const desire = parseInt(sliders.desire.input.value);
        const capability = parseInt(sliders.capability.input.value);
        const enjoyment = parseInt(sliders.enjoyment.input.value);
        const expertise = parseInt(sliders.expertise.input.value);
        const communication = parseInt(sliders.communication.input.value);

        // Update de interactieve grafiek
        desireCapabilityChart.data.datasets[0].data = [{ x: capability, y: desire }];
        desireCapabilityChart.update();

        // Bepaal de aanbeveling
        let recommendation = '';
        if (desire > 60 && capability > 60) {
            recommendation = '<strong>Sterke kandidaat voor AUTOMATISERING.</strong> Zowel de wens als de technologische capaciteit zijn hoog. Dit soort taken (vaak repetitief en niet geliefd) zijn ideaal om volledig over te dragen aan een AI-systeem.';
        } else if (capability > 50) {
            recommendation = '<strong>Goede kandidaat voor AUGMENTATIE.</strong> De technologie is capabel, maar de wens tot volledige automatisering is lager. Een AI-assistent die ondersteunt, suggesties doet of de saaie deeltaken overneemt, is hier perfect. Dit is vaak het geval bij creatieve of expert-taken.';
        } else if (desire > 50) {
             recommendation = '<strong>Wens voor de toekomst.</strong> Er is een duidelijke wens om deze taak te automatiseren, maar de technologie is er nog niet klaar voor. Dit is een gebied waar toekomstige AI-ontwikkeling veel impact kan hebben.';
        } else {
            recommendation = '<strong>Lage prioriteit voor AI.</strong> Zowel de wens als de capaciteit zijn laag. De focus kan beter liggen op andere taken. De menselijke factor (zoals plezier of complexe interactie) is hier waarschijnlijk dominant.';
        }
        
        // Voeg contextuele feedback toe
        if (communication > 70) {
            recommendation += ' <br><br><strong>Let op:</strong> Vanwege de hoge mate van interpersoonlijke communicatie is volledige automatisering riskant. Augmentatie, waarbij de AI helpt met voorbereiding of administratie, is waarschijnlijk de beste aanpak.'
        }
         if (expertise > 70) {
            recommendation += ' <br><br><strong>Let op:</strong> Omdat er veel domeinexpertise nodig is, is een "mens-in-de-lus" aanpak (augmentatie) cruciaal om de kwaliteit en juistheid te garanderen.'
        }


        // Toon de resultaten
        recommendationText.innerHTML = recommendation;
        resultsSection.classList.remove('hidden');
        resultsSection.classList.add('visible');
        
        // Scroll naar de resultaten voor een soepele ervaring
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    // Initialiseer de charts bij het laden van de pagina
    createCharts();
});
