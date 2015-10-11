<?

function err($msg) {
	throw new Exception($msg);
}

function communicate($input) {
	$port = 13579;

	set_time_limit(0);

	$sock = socket_create(AF_INET, SOCK_STREAM, SOL_TCP) or err("Failed to create socket (" . socket_strerror(socket_last_error()) . ")");

	socket_connect($sock, "localhost", $port) or err("Failed to connect socket to port $port (" . socket_strerror(socket_last_error()) . ")");

	$i = socket_write($sock, $input, strlen($input));

	if (!$i and !($i === 0)) {
		err("Failed to write (" . socket_strerror(socket_last_error()) . ")");
	}

	$result = socket_read($sock, 10240) or err("Failed to read from socket (" . socket_strerror(socket_last_error()) . ")");

	socket_close($sock);
	
	return $result;
}

function normalize($rawWeights) {
	$sum = 0;
	foreach ($rawWeights as $rawWeight) {
		$sum += $rawWeight;
	}
	$result = array();
	foreach ($rawWeights as $rawWeight) {
		$result[] = $rawWeight / $sum;
	}
	return $result;
}

if (isset($_POST['pretext'])) {
	$pretext = $_POST['pretext'];
	$history = $_POST['history'];
	$rawWeight = $_POST['rawWeight'];
	
	$weights = implode(",", normalize($rawWeight));
	
	$cmd = $weights . " $history";
	
	if (trim($pretext)) {
		$cmd .= " " . trim($pretext);
	}
	
	$text = communicate($cmd);
}
else {
	$text = "";
}


try {
	$ids = communicate("identify");
}
catch (Exception $e) {
	$ids = False;
	print "Server is offline";
	exit();
}

?>

<html>
<body>

<form method="post">

<table border="1">
<tr><td colspan="2">
	<div style="border: 1px solid black; width: 800px; height: 150px"><? print $text; ?></div>
</td></tr><tr><td colspan="2" align="center">
<input type="submit" value="Genereeri"/>
</td></tr><tr><td align="center">

<b>Teemade segu:</b><br>

<?
	$i = 0;
	
	foreach (explode(" ", $ids) as $id) {
		#weight bar / tumbler
		print "<p>$id:<br>V&auml;hem&nbsp;<input type=\"range\" name=\"rawWeight[]\" min=\"1\" max=\"100\" value=\"";
		print $rawWeight[$i];
		print "\"/>&nbsp;Rohkem</p>";
		$i++;
	}
	
	print "</td><td align=\"center\">";
	
	?>Kontekst:<br>V&auml;hem&nbsp;<input type="range" name="history" min="1" max="2" style="height:50px" value="<?
	print $history;
	print "\"/>&nbsp;Rohkem";
	
?>
</td></tr><tr><td colspan="2" align="center">
<p><b>Ettem&auml;&auml;ratud lause algus: </b><input name="pretext" style="width:620px" value="<? print $pretext; ?>"/></p>
</td></tr>
</table>

</form>
</body>
</html>
