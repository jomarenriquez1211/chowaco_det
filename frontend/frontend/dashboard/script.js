// Bar Chart
const barCtx = document.getElementById('barChart').getContext('2d');
new Chart(barCtx, {
  type: 'bar',
  data: {
    labels: ['Irrigation Systems', 'Delivery Lines'],
    datasets: [
      {
        label: 'Target',
        data: [50000, 150000],
        backgroundColor: 'rgba(100, 149, 237, 0.7)'
      },
      {
        label: 'Achieved',
        data: [60000, 280000],
        backgroundColor: 'rgba(60, 179, 113, 0.7)'
      }
    ]
  },
  options: {
    responsive: true,
    scales: {
      y: {
        beginAtZero: true
      }
    }
  }
});

// Pie Chart
const pieCtx = document.getElementById('pieChart').getContext('2d');
new Chart(pieCtx, {
  type: 'pie',
  data: {
    labels: ['Met', 'In Progress', 'Not Started'],
    datasets: [{
      data: [60, 25, 15],
      backgroundColor: [
        'rgba(60, 179, 113, 0.8)',
        'rgba(255, 206, 86, 0.8)',
        'rgba(220, 53, 69, 0.8)'
      ]
    }]
  },
  options: {
    responsive: true
  }
});
