// configurations
var margin = {top: 30, right: 30, bottom: 30, left: 30},
    width = 800 - margin.right - margin.left,
    height = 250 - margin.top - margin.bottom,
    transitionDuration = 800,
    formatDate = d3.time.format("%Y-%m-%d");

// global data structures
var data = [];
var filter = {};

// global chart objects
var brush = {};
var dateBarChart = {};
var countryBarChart = {};
var countryMap = {};

// queue all data file loading before proceeding further
queue()
  .defer(d3.csv, "data/kcna.csv")
  .defer(d3.json, "data/topo_countries.json")
  .await(ready);

// runs after all dependencies have downloaded
function ready(error, data, countries) {
  if (error) return console.error(error);

  // csv's load without type, so make date objects from dates and add indexes
  data.forEach(function(d,i) {
    d.index = i;
    d.date = formatDate.parse(d.date);
  });

  dateBarChart.dateDomain = d3.extent(data, function(d) { return d.date });

  buildCrossfilter(data, filter);

  // convert TopoJSON to plotable GeoJSON
  countryMap.data = topojson.feature(countries, countries.objects.countries);

  initialize();

  reDraw();
}

function buildCrossfilter(data, filter) {
  filter.cf = crossfilter(data);
  filter.byDate = filter.cf.dimension(function(p) { return p.date; });
  filter.groupByDate = filter.byDate.group();
  filter.byCountry = filter.cf.dimension(function(p) { return p.country; });
  filter.groupByCountry = filter.byCountry.group();
  return filter;
}

function initialize() {

  // variable declarations

  // DATE BAR CHART
  dateBarChart.scaleX = d3.time.scale()
    .domain(getDateBuffer())
    .range([0, width]);
  dateBarChart.scaleY = d3.scale.linear()
    .range([height, 0]);
  dateBarChart.scaleColor = d3.scale.linear()
    .range(colorbrewer.BuGn[3]);

  dateBarChart.axisX = d3.svg.axis()
    .scale(dateBarChart.scaleX)
    .orient("bottom")
    .ticks(10).tickFormat(formatDate);
  dateBarChart.axisY = d3.svg.axis()
    .scale(dateBarChart.scaleY)
    .orient("left")
    .ticks(3).tickFormat(d3.format("d"));

  // COUNTRY BAR CHART
  countryBarChart.scaleX = d3.scale.ordinal()
    .rangeRoundBands([0, width], 0.05);
  countryBarChart.scaleY =  d3.scale.linear()
    .range([height, 0]);
  countryBarChart.scaleColor = d3.scale.linear()
    .range(colorbrewer.OrRd[3]);

  countryBarChart.axisX = d3.svg.axis()
    .scale(countryBarChart.scaleX)
    .orient("bottom");

  countryBarChart.axisY = d3.svg.axis()
    .scale(countryBarChart.scaleY)
    .orient("left")
    .ticks(9)
    .tickFormat(d3.format("d"));

  // COUNTRY MAP
  countryMap.projection = d3.geo.mercator()
    .scale(150)
    .translate([width / 2, height / 2]);

  countryMap.path = d3.geo.path()
    .projection(countryMap.projection);

  // insert stuff on the DOM

  d3.selectAll("#charts .chart-container")
    .append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom);

  // DATE BAR CHART
  dateBarChart.gHandle = d3.select("#date-chart-container svg")
    .append("g")
    .attr("id", "date-bar-chart")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  dateBarChart.gHandle.append("g")
       .attr("class", "bars")
       .attr("id", "date-bars")
    .selectAll("rect")
       .data(filter.groupByDate.all())
       .enter()
       .append("rect")
       .attr("class", "date-bar");

  dateBarChart.gHandle.append("g")
    .attr("class", "axis")
    .attr("id", "date-axis")
    .attr("transform", "translate(0," + height + ")");

  dateBarChart.gHandle.append("g")
    .attr("class", "axis")
    .attr("id", "date-count-axis");

  // COUNTRY BAR CHART
  countryBarChart.gHandle = d3.select("#country-chart-container svg")
    .append("g")
    .attr("id", "country-bar-chart")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  countryBarChart.gHandle.append("g")
      .attr("class", "bars")
      .attr("id", "country-bars")
    .selectAll("rect")
      .data(filter.groupByCountry.all())
      .enter()
      .append("rect")
      .attr("class", "country-bar");

  countryBarChart.gHandle.append("g")
    .attr("class", "axis")
    .attr("id", "country-axis")
    .attr("transform", "translate(0," + height + ")");

  countryBarChart.gHandle.append("g")
    .attr("class", "axis")
    .attr("id", "country-count-axis");

  // COUNTRY MAP
  countryMap.gHandle = d3.select("#country-map-container svg")
    .append("g")
    .attr("class", "map")
    .attr("id", "country-map")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  countryMap.gHandle.append("path")
    .datum(countryMap.data)
    .attr("d", countryMap.path);

  // draw Background Rect For Brush
  dateBarChart.gHandle.append("rect")
    .attr("class", "grid-background")
    .attr("width", width)
    .attr("height", height);

  // draw brush
  brush = d3.svg.brush()
    .x(dateBarChart.scaleX)
    //.extent([new Date(2014, 2, 2), new Date(2014, 2, 9)])
    .extent(getBrushDefaultExtent())
    .on("brush", brushed);

  var gBrush = dateBarChart.gHandle.append("g")
    .attr("class", "brush")
    .call(brush);
  gBrush.selectAll("rect")
    .attr("y", -6)
    .attr("height", height + 7);
  gBrush.selectAll(".resize")
    .append("path")
    .attr("d", resizePath);

  // apply brushes' default extent
  filter.byDate.filterRange(brush.extent());
  reapplyFilters();
}

function reapplyFilters() {

  dateBarChart.scaleX.domain(getDateBuffer());
  dateBarChart.scaleY.domain([0,filter.groupByDate.top(1)[0].value]);
  dateBarChart.scaleColor.domain([0,filter.groupByDate.top(1)[0].value]);

  var filteredGroupByCountry = filter.groupByCountry.all().filter(function(d) { return d.value > 0; });

  countryBarChart.scaleX.domain(filteredGroupByCountry.map(function(d) { return d.key }).sort(d3.descending));
  countryBarChart.scaleY.domain([0,d3.max(filteredGroupByCountry.map(function(d) { return d.value }))]);
  countryBarChart.scaleColor.domain([0,d3.max(filteredGroupByCountry.map(function(d) { return d.value }))]);
}

function reDraw() {

  // DRAW DATE BAR GRAPH
  var dateBarWidth = (width / d3.time.days(dateBarChart.dateDomain[0],dateBarChart.dateDomain[1]).length);

  dateBarChart.gHandle.select("#date-bars")
    .selectAll("rect")
      .data(filter.groupByDate.all())
      .attr("fill", function(d) {
        return (brush.extent()[0] < d.key && d.key < brush.extent()[1] ? dateBarChart.scaleColor(d.value) : "#E3E3E3");
      })
    .transition().duration(transitionDuration)
      .attr("x", function(d, i) {
        return (dateBarChart.scaleX(d.key) - (dateBarWidth/2));
      })
      .attr("y", function(d) {
        return (dateBarChart.scaleY(d.value));
      })
      .attr("width", dateBarWidth)
      .attr("height", function(d) {
        return (height - dateBarChart.scaleY(d.value));
      });

  dateBarChart.gHandle.select("#date-axis").transition().duration(transitionDuration).call(dateBarChart.axisX);
  dateBarChart.gHandle.select("#date-count-axis").transition().duration(transitionDuration).call(dateBarChart.axisY);

  // DRAW COUNTRY BAR GRAPH
  countryBarChart.gHandle.select("#country-bars")
    .selectAll("rect")
      .data(filter.groupByCountry.all().filter(function(d) { return d.value > 0; }))
    .transition().duration(transitionDuration)
      .attr("x", function(d, i) {
          return countryBarChart.scaleX(d.key);
      })
      .attr("y", function(d) {
          return (countryBarChart.scaleY(d.value));
      })
      .attr("width", countryBarChart.scaleX.rangeBand())
      .attr("height", function(d) {
          return (height - countryBarChart.scaleY(d.value));
      })
      .attr("fill", function(d) {
          return countryBarChart.scaleColor(d.value);
      });

  countryBarChart.gHandle.select("#country-axis").transition().duration(transitionDuration).call(countryBarChart.axisX);
  countryBarChart.gHandle.select("#country-count-axis").transition().duration(transitionDuration).call(countryBarChart.axisY);
}

// Snapping behavior from http://bl.ocks.org/mbostock/6232620
function brushed() {
  var extent0 = brush.extent(),
      extent1;

  // if dragging, preserve the width of the extent
  if (d3.event.mode === "move") {
    var d0 = d3.time.day.round(extent0[0]),
        d1 = d3.time.day.offset(d0, Math.round((extent0[1] - extent0[0]) / 864e5));
    extent1 = [d0, d1];
  }

  // otherwise, if resizing, round both dates
  else {
    extent1 = extent0.map(d3.time.day.round);

    // if empty when rounded, use floor & ceil instead
    if (extent1[0] >= extent1[1]) {
      extent1[0] = d3.time.day.floor(extent0[0]);
      extent1[1] = d3.time.day.ceil(extent0[1]);
    }
  }

  d3.select(this).call(brush.extent(extent1));

  filter.byDate.filterRange(extent1);
  reapplyFilters();

  reDraw();
}

function getDateBuffer() {

  var minBuffer = 2; //days
  var maxBuffer = 2; //days

  var dateMinBuffer = new Date(dateBarChart.dateDomain[0]);
  dateMinBuffer.setDate(dateMinBuffer.getDate() - minBuffer);

  var dateMaxBuffer = new Date(dateBarChart.dateDomain[1]);
  dateMaxBuffer.setDate(dateMaxBuffer.getDate() + maxBuffer);

  return [dateMinBuffer, dateMaxBuffer];
}

function getBrushDefaultExtent() {

  var defaultRange = 14; //days

  var dateBrushMin = new Date(getDateBuffer()[1] - 12096e5);

  return [dateBrushMin, getDateBuffer()[1]];
}

// brush handles cribbed from [http://square.github.io/crossfilter/]
function resizePath(d) {
  var e = +(d == "e"),
      x = e ? 1 : -1,
      y = height / 3;
  return "M" + (.5 * x) + "," + y
      + "A6,6 0 0 " + e + " " + (6.5 * x) + "," + (y + 6)
      + "V" + (2 * y - 6)
      + "A6,6 0 0 " + e + " " + (.5 * x) + "," + (2 * y)
      + "Z"
      + "M" + (2.5 * x) + "," + (y + 8)
      + "V" + (2 * y - 8)
      + "M" + (4.5 * x) + "," + (y + 8)
      + "V" + (2 * y - 8);
}
