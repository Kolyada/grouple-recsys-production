var table_header = '<table><tbody><tr><td><b>Название манги</b></td><td><b>Ссылка</b></td></tr>';
var table_tail = '</tbody>';


function generate_row(name, link){
    substr = '';
    if (link.includes('doramatv.live')){
        substr = 'дорама'
    }else if (link.includes('readmanga.live')){
        substr = 'readmanga'
    }else if (link.includes('internal/red')){
        substr = 'mintmanga (внутренняя ссылка портала - не работает здесь)'
    }
    return '<tr><td>'+name+'</td><td><a href="'+link+'">'+substr+'</td></tr>';
}

function generate_table(data){
    table = table_header;
    for (i in data){
        row = data[i];
        table += generate_row(row[0], row[1]);
    }
    table += table_tail;
    return table;
}


function response_handler(response){
    var doc = document.getElementById('recs');
    if (response['error']){
        console.log('no such user :(');
        doc.innerHTML = 'Такой пользователь не найден. Возможные причины:<ul><li>Его не существует на портале</li><li>У него не было(/было очень мало) закладок</li><li>Он не попал в датасет</li></ul>';
    }else{
        data = response['items'];
        pairs = [];
        for (key in data){
            item = data[key];
            pairs.push([key, item]);
        }
        table = generate_table(pairs);
        
        doc.innerHTML = table;
    }
}

function request_recommendation(){
    username = document.getElementById('username_input').value;
    console.log('uname', username);
    fetch(document.location.href+"/recommend?username="+username+"&n_rec=20")
    .then(function (response) {
        return response.json();
    })
    .then(function (myJson) {
        response_handler(myJson);
    })
}