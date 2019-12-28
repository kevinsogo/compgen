#!/usr/bin/env php
<?php declare(strict_types=1);

require('/opt/domjudge/domserver/etc/domserver-static.php');
require(ETCDIR . '/domserver-config.php');
require(LIBDIR . '/init.php');

setup_database_connection();

$stdin = fopen('php://stdin', 'r');

$count = 0;

while (fscanf(STDIN, "%s\n", $username)) {
    fscanf(STDIN, "%s\n", $password);
    fscanf(STDIN, "%[^\n]s\n", $school);
    fscanf(STDIN, "%[^\n]s\n", $school_short);
    fscanf(STDIN, "%s\n", $country_code);
    fscanf(STDIN, "%[^\n]s\n", $display_name);

    echo "Got username $username for team: '$display_name'\n";

    // get affiliation ID, or insert if it doesn't exist yet
    try {
        $affil_id = $DB->q("VALUE SELECT affilid FROM team_affiliation WHERE name = %s and country = %s LIMIT 1", $school, $country_code);
    } catch (exception $e) {
        $affil_id = $DB->q("RETURNID INSERT INTO team_affiliation (name, shortname, country) VALUES (%s, %s, %s)", $school, $school_short, $country_code);
        echo "Creating new affiliation: $school ($school_short) from $country_code\n";
    }

    $team_id = $DB->q("RETURNID INSERT INTO team (name, affilid, categoryid) VALUES (%s, %s, %i)", $display_name, $affil_id, 3);
    $user_id = $DB->q("RETURNID INSERT INTO user (username, name, password, teamid) VALUES (%s, %s, %s, %i)", $username, $display_name, dj_password_hash($password), $team_id);
    $DB->q("INSERT INTO userrole (userid, roleid) VALUES(%i, %i)", $user_id, 3);
    echo "Added $username\n\n";
    $count++;
}
echo "Done. Added $count teams.\n";
