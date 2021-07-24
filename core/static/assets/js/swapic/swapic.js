<!-- USER WANTS TO SEE SWAP DETAILS -->

//    $('#message_box').attr('class', 'mt-3 text-center alert alert-' + data.status)
//    $('#message_text').text(data.message);


var receive_method_screen = $('#receive_method_screen');
var result_screen_1 = $('#result_screen_1');
var receive_method = 'wallet';
var details_table = $('#details_table');
var b_details = $('#details_button');


receive_method_screen
class ScreenManager {
  constructor(screen) {
    this.screen = screen;
    this.is_visible = false;
  }

  toggle() {
    console.log('TOGGLING')
    if (this.is_visible) {
        this.screen.fadeOut(100);
        this.is_visible = false;
    } else {
        this.screen.fadeIn(400);
        this.is_visible = true;
    }
  }
}

class ButtonManager {
    constructor(button) {
        this.button = button;
        this.text = "";
        this.color = "";
        this.set_text('Provide amounts');
        this.deny_swap();
    }

    set_text(txt) {
        this.text = txt;
        this.button.text(this.text);
        console.log(txt)
    }
    set_color(color) {
        this.button.removeClass(this.color);
        this.color = color;
        this.button.addClass(this.color);
        console.log(color)
    }
}

class SwapButton extends ButtonManager {
    allow_swap() {
        this.text = "Continue";
        this.set_color('btn-success');
        this.button.text(this.text);
        this.button.prop('disabled', false);
        this.button.click(function() {receiveMethod()})
    }
    deny_swap() {
        this.set_color('');
        this.text = 'Please provide amounts';
        this.button.text(this.text);
        this.button.prop('disabled', true);
    }
}


var dt = new ScreenManager(details_table);
var rs1 = new ScreenManager(result_screen_1);
var rm1 = new ScreenManager(receive_method_screen);


var b_swap = new SwapButton($('#buy_button'));

$(document).ready(function() {
    b_details.click(function() {
        dt.toggle()
    });

//    sendMessage(msg="PROVIDE AMOUNTS")
//    b_swap.button.click(function() {
//        rs1.toggle()
//        if (rs1.is_visible) {
//            b_swap.set_text("Hide details");
//            b_swap.set_color("btn-secondary");
//        } else {
//            b_swap.set_text("Check details");
//            b_swap.set_color("btn-success");
//        }
//    });
});

function sendMessage(msg, color=false) {
    message_box = $('#message_box');
    message_txt = $('#message_text')
    message_txt.text(msg);
    if (color) {
        message_box.attr('class', 'mt-3 text-center alert alert-' + color)
    }
};

function toggleHide(elem_id, kill=0) {
    console.log('Clicked' + elem_id);
    $(elem_id).fadeToggle(200);

    console.log(kill)
    if (kill !== 0) {
        console.log('kill trigger')
        $(kill).addClass('epic_hide');
    };
};

$('#spend').keyup(function () {
    update_spend()
});

$('#buy').keyup(function () {
    update_buy()
});

$('#confirm_send_button').click(function() {
    Clock.pause();
    goSummaryPage()
});

$('#receive_wallet_button').click(function() {
    receive_method = 'wallet';
    $(this).prop('active', 'true');
    $('#receive_method_text').text("Wallet:");
    $('#receive_help_text').html('Provide Epic-Cash wallet address registered in <a href="https://github.com/fastepic/epicwallet"> Epic-Cash GUI wallet. </a> <p class="text-right"> <a href="#" class="text-muted">More information</a></p>');
    $('#receive_input').prop('placeholder', " address");

});

$('#receive_keybase_button').click(function() {
    receive_method = 'keybase';
    $(this).prop('active', 'true');
    $('#receive_method_text').text("Keybase: ");
    $('#receive_help_text').html("Please give your Keybase.io unique username, you will have access to bought Epic-Cash coins through communicator.");
    $('#receive_input').prop('placeholder', " username");
});

$('#confirm_buy_button').click(function() {
    $('#user_address').toggleClass('epic_hide');
});

<!-- USER HAVE TO PROVIDE RECEIVING METHOD -->

function receiveMethod() {
    rs1.toggle()

    rm1.toggle()
}


<!-- USER ACCEPTED TERMS BEFORE SENDING QUOTA ASSET -->

function userAccepted() {
    Clock.restart()
    var csrf = $('input[name=csrfmiddlewaretoken]').val();
    currency = "XLM",
    epic = $('#buy').val(),
    xlm = $('#spend').val(),
    receive_input_adr = $('#receive_input').val(),
    $.ajax({
        type: "POST",
        url: 'trader/tx/',
        data : {
             csrfmiddlewaretoken: csrf,
             receive_address: receive_input_adr,
             receive_method: receive_method,
             epic: epic,
             xlm: xlm,
            },
            success:function(data) {
               console.log(data);
               $("#receive_page").toggleClass('epic_hide');
               $("#send_page").fadeIn(1000);
               $("#send_amount").text(xlm + " XLM" );
               $("#send_address").text(data.send_address);
               $("#send_memo").text(data.memo);
            }
    });
};

<!-- USER CONFIRMED AND SENT QUOTA ASSET -->

function goSummaryPage() {
    toggleHide('#send_page');
    toggleHide('#receive_page');
    toggleHide('#stellar_result_table');
    toggleHide('#summary_page');
    var csrf = $('input[name=csrfmiddlewaretoken]').val();

    $.ajax({
        type: "GET",
        url: '/user_confirmed',
        data : {
             csrfmiddlewaretoken: csrf,
             status: 'user_confirmed'
            },
            success:function(data) {
                console.log(data)
                if (data.status === 'DONE') {
                   $('#loading_text').html('<span style="font-size: 7rem" class="text-success material-icons">task_alt</span>');
                } else {
                   $('#loading_text').html('<span style="font-size: 7rem" class="text-warning material-icons">schedule</span>');
                }
        },
    });
};

function updateStellarTableResult() {
    // SPINNER ON
    $('#result_spinner').addClass('spinner-grow')

    var csrf = $('input[name=csrfmiddlewaretoken]').val();
    currency = "XLM",
    buy = $('#buy').val(),
    spend = $('#spend').val(),
    $.ajax({
        type: "POST",
        url: 'trader/',
        data : {
             csrfmiddlewaretoken: csrf,
             currency: currency,
             spend: spend,
             side: 'buy',
             buy: buy,
            },
            success:function(data) {
                console.log(data);
                const progressBar = document.querySelector('.progress');
                const bar = progressBar.querySelector('.price_impact_bar')
                let progress = data.impact.toFixed(1);
                if (progress >= 100) {
                    bar.style.width = '100%';
                  } else {
                  console.log(progress)
                    bar.style.width = progress + '%';
                  }

                // TABLE HEAD
                $('#result_buy').text(parseFloat(buy).toLocaleString('en') + " " + " EPIC");
                $('#result_pay').text(data.total.toLocaleString('en') + " " + data.pair);
                $('#result_pay_usd').text("~ " + parseFloat(data.total_counter).toLocaleString('en') + " " + data.counter);
                $('#result_price').text(data.average + " " + data.pair);
                $('#result_price_usd').text("~ " + data.average_counter + " " + data.counter);


                // $('.result_buy').text(data.pair + "-EPIC");
                // $(".th2").text(data.side + " " + parseFloat($("#buy").val()).toLocaleString('en') + " EPIC");

                // TABLE BODY
                $(".td11").text("Start price: ");
                $(".td12").text(data.start_price + " " + data.pair);
                $(".td13").text("~ " + data.start_price_counter + " " + data.counter);
                $(".td21").text("Average price: ");
                $(".td22").text(data.average + " " + data.pair);
                $(".td23").text("~ " + data.average_counter + " " + data.counter);
                $(".td31").text("New price: ");
                $(".td32").text(data.new_price + " " + data.pair);
                $(".td33").text("~ " + data.new_price_counter + " " + data.counter);
                $(".td41").text("Total: ");
                $(".td42").text(data.total.toLocaleString('en') + " " + data.pair);
                $(".td43").text("~ " + parseFloat(data.total_counter).toLocaleString('en') + " " + data.counter);
                $(".td51").text("Impact:");
                $(".td53").text(parseFloat(data.impact.toFixed(2)).toLocaleString('en') + "%");

                // SPINNER OFF
                $('#result_spinner').removeClass('spinner-grow')

        },
        error : function(xhr,errmsg,err) {
        $('#results').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: "+errmsg+
            " <a href='#' class='close'>&times;</a></div>"); // add the error to the dom
        console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        },

    });
};

<!-- UPDATE VALUES BASED ON QUOTA ASSET CHANGES -->

function isPositiveFloat(s) {
  return !isNaN(s) && Number(s) > 0;
}

function update_spend () {
    currency = "XLM",
    spend = $('#spend').val(),
    $.ajax({
        type: "GET",
        url: 'xlm_sepic_json/',
        data : {
             currency: currency,
             spend: spend,
            },
            success:function(data) {
                console.log(data);
                price = parseFloat(data.value.xlm_to_epic).toFixed(2);
                $('#buy').val(price);

                // UPDATE BASED ON SPEND VALUE (IF spend > 0)
                if (isPositiveFloat(spend)) {
                    updateStellarTableResult();
                    b_swap.allow_swap();
                    if (!rs1.is_visible) {
                        rs1.toggle()
                    }
                } else {
                    if (rs1.is_visible) {
                        rs1.toggle()
                    }
                    b_swap.deny_swap();
                };
            },
    });
};

// pay / avg = buy
// avg * buy = pay


<!-- UPDATE VALUES BASED ON BUYING ASSET CHANGES -->

function update_buy () {
    currency = "EPIC",
    buy = $('#buy').val(),
    $.ajax({
        type: "GET",
        url: 'xlm_sepic_json/',
        data : {
             currency: currency,
             buy: buy,
            },
            success:function(data) {
                console.log(data);
                price = parseFloat(data.value.epic_to_xlm).toFixed(2);
                $('#spend').val(price);
                updateStellarTableResult()

                // UPDATE BASED ON BUY VALUE (IF buy > 0)
                if (isPositiveFloat(buy)) {
                    updateStellarTableResult();
                    b_swap.allow_swap();
                    if (!rs1.is_visible) {
                        rs1.toggle()
                    }
                } else {
                    if (rs1.is_visible) {
                        rs1.toggle()
                    }
                    b_swap.deny_swap();
                };
            }
    });
};

$(function() {
    $('.private_key').click(function() {
        $(this).toggleClass('epic_hide_text');
    });
});

$(function() {
    $('.public_key').click(function() {
        $(this).toggleClass('epic_hide_text');
    });
});