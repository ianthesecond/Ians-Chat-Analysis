// When the analyse button is clicked:
document.getElementById("analyse").onclick = function() {
    var textFileInput = document.getElementById("textFile");
    var form = document.getElementById("form");
    
    // Simulate the click of file input and submit the file once chosen to the server with Ajax
    textFileInput.click();
    textFileInput.onchange = function submitFunction() {
        // Create a form to be sent with Ajax and create and Ajax request
        var formData = new FormData(form);
        var xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function () {
            // If the data is being processed, show spinner
            if (this.readyState < 4) {
                spinnerToggle(true);
            }
            // If the server responded with OK and the request is complete, render that chart
            // and close the spinner
            if (this.readyState == 4 && this.status == 200) {
                spinnerToggle(false);
                response = this.responseText;
                analysisDataObject = JSON.parse(response);
                renderAnalysisCharts(analysisDataObject);
            } // If the request is complete and there's an error, alert (with a modal) the user
            else if (this.readyState == 4 && (this.status == 400 || this.status == 500)) {
                response = this.responseText;
                errorMessage = JSON.parse(response)["error"];
                document.getElementById("errorMessage").innerHTML = errorMessage;
                $('#errorModal').modal('show');
                
            }
        };
        // Open and send the Ajax request
        xhttp.open("POST", form.getAttribute("action"), true);
        xhttp.send(formData);
        
        // Return false as to not do the default action of form submition
        return false;
    };
}


// Function to show or hide spinner while hiding and showing the analyse button, respecively. 
function spinnerToggle(show) {
    if (show == true) {
        $("#form").fadeOut("slow", function() {
            $("#spinner").fadeIn()
        })
    } else {
        $("#spinner").fadeOut("slow", function() {
            $("#form").fadeIn()
        })
    };
};

// Plot the charts data
function renderAnalysisCharts(analysisDataObject) {
    // Get the authors container and the authors value, then insert into the container
    var authorsContainer = document.getElementById("authors");
    var authors = analysisDataObject["authors"].join(", ");
    authorsContainer.insertAdjacentHTML("afterbegin", authors);
    
    // Insert the start and end date value into the container
    var startDate = moment(analysisDataObject["timespan"]["startDate"]);
    var endDate = moment(analysisDataObject["timespan"]["endDate"]);
    document.getElementById("startDate").innerHTML = startDate.format("LL");
    document.getElementById("endDate").innerHTML = endDate.format("LL");

    // Loop through totals values (days, messages, words, letters) and insert into the container
    totalsKeys = Object.keys(analysisDataObject["totals"]);
    for (const key of totalsKeys) {
        if (key == "totalDays") {
            document.getElementById(key).innerHTML = analysisDataObject["totals"][key];
        } else { // Note that key is a variable that could be [messages, letters, words]
            totalKeyContainer = document.getElementById(key)
            totalKeyPerAuthor = Object.entries(analysisDataObject["totals"][key])
            for (var [author, Key] of totalKeyPerAuthor) {
                // When inserting, put some HTML as well for layout and styling
                author = "<h4 class='d-inline'>" + author + ": " + "</h4>"
                Key = "<span>" + Key + "</span>"
                authorKey = author + Key
                totalKeyContainer.insertAdjacentHTML("beforeend", '<div class="value">' + authorKey + '</div>')
            };
        }
    }

    // Loop through the avereges values and insert into container
    averagesKeys = Object.keys(analysisDataObject["averages"]);
    for (const key of averagesKeys) {
        document.getElementById(key).innerHTML = analysisDataObject["averages"][key];
    }
     
    // Insert the values of most active day
    var dateOfMostactiveDay = moment(analysisDataObject["mostActiveDay"]["date"])
    document.getElementById("dateOfMostActiveDay").innerHTML = dateOfMostactiveDay.format("LL");
    document.getElementById("messagesOfMostActiveDay").innerHTML = analysisDataObject["mostActiveDay"]["messages"]
    document.getElementById("wordsOfMostActiveDay").innerHTML = analysisDataObject["mostActiveDay"]["words"]

    
    // Insert the values of most relevant words
    var mostRelevantWordsPerAuthor = Object.entries(analysisDataObject["mostRelevantWords"]);
    for (const [author, mostRelevantWords] of mostRelevantWordsPerAuthor) {
        // Join the relevant words
        var wordsHTML = mostRelevantWords.join(", ");
        // Pait the author and their relevant words (with some html for layout and styling) and insert into container
        var relevantWordsAuthor = '<div class="col">\n<h4>' + author + '</h4>\n<div class="value"><p class="relevantWords">' + wordsHTML + '</p></div>\n</div>';
        document.getElementById("mostRelevantWordsContainer").insertAdjacentHTML("beforeend", relevantWordsAuthor);
    }

    // set the Charts default title options
    Chart.defaults.global.title.fontColor = "#1F1F1F";
    Chart.defaults.global.title.fontFamily = 'Source Sans Pro';
    Chart.defaults.global.title.fontStyle = 'normal'
    Chart.defaults.global.title.fontSize = 16


    // Render the chart with Chart.JS
    var timelineChartCanvas = document.getElementById("timelineChartCanvas").getContext("2d");
    var timelineChart = new Chart(timelineChartCanvas, {
        type: "bar",
        data: analysisDataObject["timelineChartData"],
        options: {
            scales: {
                xAxes: [{
                    stacked: true,
                    type: "time",
                    distribution: "linear"
                }],
                yAxes: [{
                stacked: false,
                ticks: {
                    beginAtZero: true,
                },
                }]
            },
            responsive: true,
            tooltips: {
                mode: "index",
            }
        }
    });
    //
    //
    //
    var messagesComparisonChartCanvas = document.getElementById("messagesComparisonChartCanvas").getContext("2d");
    var messagesComparisonChart = new Chart(messagesComparisonChartCanvas, {
        type: "doughnut",
        data: analysisDataObject["messagesComparisonChartData"],
        options: {
            aspectRatio: 1,
            responsive: true,
            title: {
                display: true,
                text: "Messages Comparison",
                
            },
            legend: {
                display: false
            }
        }
    });
    //
    //
    //
    var wordsComparisonChartCanvas = document.getElementById("wordsComparisonChartCanvas").getContext("2d");
    var wordsComparisonChart = new Chart(wordsComparisonChartCanvas, {
        type: "doughnut",
        data: analysisDataObject["wordsComparisonChartData"],
        options: {
            aspectRatio: 1,
            responsive: true,
            title: {
                display: true,
                text: "Words Comparison",
            },
            legend: {
                display: false
            }
        }
    });
    //
    //
    //
    var dayActivityChartCanvas = document.getElementById("dayActivityChartCanvas").getContext("2d");
    var dayActivityChart = new Chart(dayActivityChartCanvas, {
        type: "radar",
        data: analysisDataObject["dayActivityChartData"],
        options: {
            aspectRatio: 1,
            responsive: true,
            tooltips: {
                mode: "index",
            },
            title: {
              display: true,
              text: "Day Activity",
            },
            legend: {
                display: false
            }
        }
    });
    //
    //
    //
    var weekActivityChartCanvas = document.getElementById("weekActivityChartCanvas").getContext("2d");
    var weekActivityChart = new Chart(weekActivityChartCanvas, {
        type: "radar",
        data: analysisDataObject["weekActivityChartData"],
        options: {
            responsive: true,
            aspectRatio: 1,
            tooltips: {
                mode: "index",
            },
            scale: {
                ticks: {
                    beginAtZero: true
                }
            },
            title: {
                display: true,
                text: "Week Activity",
              },
            legend: {
                display: false
            }
        }
    });
    //
    //
    //
    var topWordsChartCanvas = document.getElementById("topWordsChartCanvas").getContext("2d");
    var topWordsChart = new Chart(topWordsChartCanvas, {
        type: "horizontalBar",
        data: analysisDataObject["topWordsChartData"],
        options: {
            scales: {
                yAxis: [{
                    stacked: true
                }],
                yAxes: [{
                    stacked: true
                }]
            },
            aspectRatio: 0.5
        }
    });
    //
    //
    //
    if (analysisDataObject["topEmojisChartData"] != null) {
        var topEmojisChartCanvas = document.getElementById("topEmojisChartCanvas").getContext("2d");
        var topEmojisChart = new Chart(topEmojisChartCanvas, {
            type: "line",
            data: analysisDataObject["topEmojisChartData"],
            options: {
                responsive: true,
                tooltips: {
                    mode: "index",
                }
            }
        });
    }
    

    // Show the charts container and smooth scroll to the top of the container
    $("#analysisContainer").collapse("toggle");
    $('html, body').animate({
        scrollTop: $("#analysisContainer").offset().top
    }, 1500);
}




