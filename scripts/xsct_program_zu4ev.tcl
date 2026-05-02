proc required_env {name} {
    if {![info exists ::env($name)] || $::env($name) eq ""} {
        error "Missing required environment variable: $name"
    }
    return $::env($name)
}

proc select_target {label patterns} {
    foreach pattern $patterns {
        if {![catch {targets -set -nocase -filter "name =~ \"$pattern\""} result]} {
            puts "PROGRAM|selected|$label|$pattern"
            return
        }
    }
    error "Unable to select target $label"
}

proc configure_fpga {bit_path} {
    foreach pattern {"PL" "xczu4"} {
        if {![catch {targets -set -nocase -filter "name =~ \"$pattern\""}]} {
            if {![catch {fpga -file $bit_path} msg]} {
                puts "PROGRAM|fpga|configured|$pattern"
                return
            }
        }
    }
    error "Unable to configure PL with bitstream $bit_path"
}

set server_url [required_env HW_SERVER_URL]
set bit_path [file normalize [required_env BIT_PATH]]
set pmufw_path [file normalize [required_env PMUFW_PATH]]
set fsbl_path [file normalize [required_env FSBL_PATH]]
set app_path [file normalize [required_env APP_ELF_PATH]]
set psu_init_path [file join [file dirname $bit_path] psu_init.tcl]

connect -url $server_url
targets

if {[file exists $psu_init_path]} {
    source $psu_init_path
    puts "PROGRAM|psu_init|sourced|[file nativename $psu_init_path]"
} else {
    puts "PROGRAM|psu_init|missing|[file nativename $psu_init_path]"
}

select_target "PSU" {"PSU"}
rst -system
after 1000
select_target "PSU" {"PSU"}
mwr 0xffca0038 0x1ff
after 500

select_target "PMU" {"MicroBlaze PMU" "PMU"}
dow $pmufw_path
con
after 1000

select_target "A53_0" {"Cortex-A53 #0"}
rst -processor
dow $fsbl_path
con
after 5000
stop

configure_fpga $bit_path
after 500

if {[llength [info commands psu_ps_pl_reset_config]] > 0} {
    select_target "PSU" {"PSU"}
    if {[llength [info commands psu_post_config]] > 0} {
        psu_post_config
        puts "PROGRAM|psu_post_config|done"
    }
    if {[llength [info commands psu_protection]] > 0} {
        psu_protection
        puts "PROGRAM|psu_protection|done"
    }
    psu_ps_pl_reset_config
    psu_ps_pl_isolation_removal
    puts "PROGRAM|ps_pl|enabled"
    after 500
}

select_target "A53_0" {"Cortex-A53 #0"}
rst -processor
dow $app_path
con
puts "PROGRAM|run|started"
after 1000

disconnect
exit
