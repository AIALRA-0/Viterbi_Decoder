proc required_env {name} {
    if {![info exists ::env($name)] || $::env($name) eq ""} {
        error "Missing required environment variable: $name"
    }
    return $::env($name)
}

set workspace [file normalize [required_env XSCT_WORKSPACE]]
set platform_name [required_env PLATFORM_NAME]
set xsa_path [file normalize [required_env XSA_PATH]]

file mkdir $workspace
setws $workspace

set platform_dir [file join $workspace $platform_name]
if {[file exists $platform_dir]} {
    file delete -force $platform_dir
}

platform create -name $platform_name -hw $xsa_path -proc psu_cortexa53_0 -os standalone -out $workspace
platform active $platform_name
platform generate

set platform_dir [file normalize [file join $workspace $platform_name]]
set xsa_base [file rootname [file tail $xsa_path]]
set bit_path [file join $platform_dir hw ${xsa_base}.bit]
set fsbl_path [file join $platform_dir zynqmp_fsbl fsbl_a53.elf]
set pmufw_path [file join $platform_dir zynqmp_pmufw pmufw.elf]
set bsp_root [file join $platform_dir psu_cortexa53_0 standalone_domain bsp psu_cortexa53_0]

puts "XSCT_PLATFORM|dir|[file nativename $platform_dir]"
puts "XSCT_PLATFORM|bit|[file nativename $bit_path]"
puts "XSCT_PLATFORM|fsbl|[file nativename $fsbl_path]"
puts "XSCT_PLATFORM|pmufw|[file nativename $pmufw_path]"
puts "XSCT_PLATFORM|bsp|[file nativename $bsp_root]"

exit
