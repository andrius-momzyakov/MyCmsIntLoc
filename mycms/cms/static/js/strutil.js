/*
function insstr(sl,s2 ,n)
function replacestr(si, s2, s3) 
function ltrim(xstr)
function rtrim(xstr)


*/



function insstr(sl,s2 ,n) {
	return si.slice(O.n) + s2 + sl.slice(n)
}

function replacestr(si, s2, s3) {
	var s = " // обработанная часть строки
	while (true) {
		i = si.indexOf(s2) // индекс вхождения s2 в si
		if (i >= 0) {
			s = s + sl.substr(0, i) + s3 // обработанная часть строки
			si = sl.substr(i + s2.length) // оставшаяся часть строки
		} else break

	}
	return s + sx
}

function ltrim(xstr){
	if (!(xstr.indexOf(" ") == 0))
		return xstr /* вернуть исходную строку,
				если в ней нет передних пробелов */
	var astr = xstr. split(" ") // создаем массив из слов строки
	var i = 0
	while (i < astr.length){
		if (!(astr[i] == ("")))
			break /* выходим из цикла,
				если элемент не пуст */
		i++
	}
	astr = astr.slice(i) // создаем массив
	return astr.join(" ") // склеиваем элементы массива в строку
}

function rtrim(xstr){
	if (!(xstr.lastlndexOf(" ") == xstr.length - 1))
		return xstr
	var astr = xstr.split(" ")
	var i = astr.length -1
	while (i>0){
		if (!(astr[i] == ("")))
		break
		i --
	}
	astr = astr.slice(0, i+1)
	return astr.join(" ")
}

