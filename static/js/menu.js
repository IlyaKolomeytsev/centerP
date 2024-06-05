var citizensP = document.querySelectorAll('.citizensP')[0];
var citizensPWork = document.querySelectorAll('.citizensPWork')[0];
var citizensPSite = document.querySelectorAll('.citizensPSite')[0];
var three = document.querySelectorAll('.three')[0];
var body = document.querySelectorAll('body')[0];

function oneFunctionIv(event) {
    if(event.target.classList.value == 'citizensP' || event.target.className == 'one' || event.target.className == 'contentDiv' || event.target.className == 'citizensPDiv') {
        citizensP.classList.add('visible');
        citizensP.classList.remove('invisible');
    } else {
        citizensP.classList.remove('visible');
        citizensP.classList.add('invisible');
    }

    if(event.target.classList.value == 'citizensPWork' || event.target.className == 'two' || event.target.className == 'contentDiv1' || event.target.className == 'citizensPDivWork') {
        citizensPWork.classList.add('visible');
        citizensPWork.classList.remove('invisible');
    } else {
        citizensPWork.classList.remove('visible');
        citizensPWork.classList.add('invisible');
    }
}

function threeFun() {
    window.open('https://www.consultant.ru/document/cons_doc_LAW_34683/', '_blank');
}

body.addEventListener('mousemove', oneFunctionIv);
three.addEventListener('click', threeFun);