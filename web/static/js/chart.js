function setChartLength(seconds){
    chartLength = seconds;
    let labels = new Array();
    for (let i = 0; i <= seconds; i++) {
        labels[i] = i;
    }
    chart.data.labels = labels;
    chart.update();
}

function setTargetTempInChart(temperaturePoints){
    temperaturePoints.sort(sortFunction);
    if(temperaturePoints.at(-1)[0] > chartLength){
        setChartLength(temperaturePoints.at(-1)[0]);
    }
    // add a Point (0, 0), if the target temperature chart doesn't start at time 0s.
    if(temperaturePoints[0][0] != 0){
        temperaturePoints = [[0, 0]].concat(temperaturePoints);
        console.log(temperaturePoints)
    }
    chart.data.datasets[0].data = temperaturePoints;
    chart.update();
}

function setMeasuredTempInChart(temperaturePoints){
    if(temperaturePoints.length > 0 && temperaturePoints.at(-1)[0] > chartLength){
        setChartLength(temperaturePoints.at(-1)[0]);
    }
    chart.data.datasets[1].data = temperaturePoints;
    chart.update();
}

function addMeasuredTempPointInChart(temperaturePoint){
    if(temperaturePoint[0] > chartLength){
        setChartLength(temperaturePoint[0]);
    }
    chart.data.datasets[1].data.push(temperaturePoint);
    chart.update();
}

function clearTargetTempInChart(){
     chart.data.datasets[0].data = new Array();
     chart.update();
}

function clearMeasuredTempInChart(){
     chart.data.datasets[1].data = new Array();
     chart.update();
}

const ctx = document.getElementById('reflow_chart');

const data = {
  labels: [],
  datasets: [{
    label: 'Target temperature',
    data: [],
    fill: false,
    borderColor: 'rgb(00, 147, 116)',
    pointStyle: 'circle',
    pointRadius: 10,
    pointHoverRadius: 15,
    backgroundColor: 'rgb(00, 147, 116)',
    tension: 0.1,
  },
  {
    label: 'Measured temperature',
    data: [],
    fill: true,
    borderColor: 'rgb(31, 130, 192)',
    tension: 0.1
  }]
};


chart = new Chart(ctx, {
  type: 'line',
  data: data,
  options: {
    responsive: true,
    plugins: {
      title: {
        display: false,
        text: 'Chart with Tick Configuration'
      }
    },
    scales: {
      x: {
        ticks: {
          // For a category axis, the val is the index so the lookup via getLabelForValue is needed
          callback: function(val, index) {
            // Hide every 2nd tick label
            return index % 5 === 0 ? this.getLabelForValue(val) : '';
          },
        }
      }
    },
    animation: {
        duration: 0
    }
  },

});
