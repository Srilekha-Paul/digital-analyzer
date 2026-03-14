// const ctx = document.getElementById("chart");

// new Chart(ctx,{
// type:"bar",
// data:{
// labels:apps,
// datasets:[{
// label:"Usage Time",
// data:times,
// backgroundColor:"#6366F1"
// }]
// }
// });

// const ctx = document.getElementById("chart");

// new Chart(ctx, {
// type: "bar",
// data: {
// labels: window.apps,
// datasets: [{
// label: "Usage Time (seconds)",
// data: window.times,
// backgroundColor: [
// "#667eea",
// "#764ba2",
// "#32ff7e",
// "#ff9f43",
// "#ff6b6b"
// ]
// }]
// },
// options: {
// responsive:true,
// plugins:{
// legend:{
// labels:{
// color:"white"
// }
// }
// },
// scales:{
// x:{
// ticks:{color:"white"}
// },
// y:{
// ticks:{color:"white"}
// }
// },
// animation:{
// duration:2000,
// easing:'easeOutBounce'
// }
// }
// });




// const scoreElement = document.getElementById("score");
// const target = parseInt(scoreElement.innerText);

// let count = 0;

// const counter = setInterval(() => {

// count++;

// scoreElement.innerText = count + "%";

// if(count >= target){
// clearInterval(counter);
// }

// },20);


const ctx = document.getElementById("chart");

new Chart(ctx, {

type: "bar",

data: {

labels: window.apps,

datasets: [{

label: "Usage Time",

data: window.times,

backgroundColor: [

"#667eea",
"#764ba2",
"#32ff7e",
"#ff9f43",
"#ff6b6b"

]

}]

},

options: {

responsive:true,

animation:{
duration:1500
}

}

});