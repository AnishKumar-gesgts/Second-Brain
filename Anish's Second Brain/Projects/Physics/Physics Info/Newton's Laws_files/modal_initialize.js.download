/**
 * Initialization modal for Platform users that don't have AoPS accounts.
 */

AoPS.Utils.initKeyChain(AoPS, "Initialize");

AoPS.Initialize = (function (Initialize) {
	Initialize.Models = {};
	Initialize.Views = {};

	Initialize.Models.Master = AoPS.Model.extend({});

	Initialize.Views.Initialize = AoPS.View.extend({
		template_id: "#modal-initialize-tpl",
		initialize: function () {
			var platformUser = AoPS.bd.platform_user_info;
			this.vars = {
				username: platformUser.username,
				usernameApplicationCode: platformUser.username_application_code,
				hasGlobalUsername:
					!!platformUser.username && !platformUser.username_application_code,
				email: platformUser.email,
				bypassesCoppa:
					platformUser.bypasses_coppa ||
					AoPS.session.is_coppa_approved ||
					AoPS.bd.has_academy_enrollments,
				emailRequired: !platformUser.email,
			};
			this.setupCalendar();
			this.render();
		},
		render: function () {
			this.$el.html(this.getTemplate(this.template_id, this.vars));
			this.setupListeners();
		},
		getTemplate: function (template_id, vars) {
			// This is a bootstrapped handlebars template, it's safe to display.
			// ignore-security-checks
			var $templates = $("<div />").html(AoPS.bd.initialize_tpl);
			var $tpl = $templates.find(template_id);
			var compiledTpl = Handlebars.compile($tpl.html());
			var parsedTpl = $.parseHTML(compiledTpl(vars));
			return parsedTpl;
		},
		setupCalendar: function () {
			this.vars.calendarDays = [];
			for (var i = 1; i <= 31; i++) {
				this.vars.calendarDays.push(i);
			}

			this.vars.calendarYears = [];
			var thisYear = moment().year();
			var minYear = thisYear - 100;
			for (var j = thisYear - 3; j >= minYear; j--) {
				this.vars.calendarYears.push(j);
			}
		},
		setupListeners: function () {
			// If the user starts typing in a new username, auto-select the
			// radio button for a new username.
			this.$el.find("#new-username-input").on(
				"click change keyup",
				function () {
					this.$el.find("#new-username-radio").prop("checked", true);
				}.bind(this)
			);

			// Main submit button.
			this.$el
				.find("#initialize-btn")
				.on("click", this.onClickInitialize.bind(this));
		},
		onClickInitialize: function () {
			this.showLoadingModal();
			this.clearAllErrors();

			var hasErrors = false;
			var usernameRes = this.validateUsername();
			if (usernameRes.error) {
				hasErrors = true;
				this.showError("username", usernameRes.error);
			}

			var emailRes = this.validateEmail();
			if (emailRes.error) {
				hasErrors = true;
				this.showError("email", emailRes.error);
			}

			// Get the birthday info. Validation happens on the backend, no
			// need to do it on the frontend too.
			var month = parseInt(this.$el.find("#select-month").val());
			var day = parseInt(this.$el.find("#select-day").val());
			var year = parseInt(this.$el.find("#select-year").val());

			if (!hasErrors) {
				$.ajax({
					url: "/m/user/ajax.php",
					timeout: 10000,
					method: "POST",
					data: {
						action: "initialize",
						username: usernameRes.username,
						email: emailRes.email,
						day: day,
						month: month,
						year: year,
					},
					success: _.bind(function (data) {
						this.closeLoadingModal();
						if (data.response.success) {
							AoPS.Ui.Modal.closeAllModals();
							this.vars.isCoppa = data.response.is_coppa;
							this.vars.needsEmailVerification =
								data.response.needs_email_verification;
							this.renderSuccessModal();
						} else {
							if (data.error_code === "E_INVALID_USERNAME") {
								this.showError("username", data.error_msg);
							} else if (data.error_code === "E_INVALID_BIRTHDAY") {
								this.showError("birthday", data.error_msg);
							} else if (data.error_code === "E_INVALID_EMAIL") {
								this.showError("email", data.error_msg);
							} else {
								this.showError("unknown", data.error_msg);
							}
						}
					}, this),
					error: _.bind(function (data) {
						this.showError("unknown", data.error_msg);
						this.closeLoadingModal();
					}, this),
				});
			} else {
				this.closeLoadingModal();
			}
		},
		clearAllErrors: function () {
			var $errorEls = this.$el.find(".error-msg");
			for (var el of $errorEls) {
				$(el).text("");
			}
		},
		showError: function (field, error) {
			if (!error) {
				error = "Something went wrong. Please try again later.";
			}
			var $errorDiv = this.$el.find(`#${field}-error`);
			$errorDiv.text(error);
		},
		renderSuccessModal: function () {
			this.$el.html(
				this.getTemplate("#modal-initialize-success-tpl", this.vars)
			);
			AoPS.Ui.Modal.showAlert(this.$el, {
				onClose: function () {
					window.location.reload();
				},
			});
		},
		validateUsername: function () {
			// If the user had to choose a username
			if (!this.vars.hasGlobalUsername) {
				var enteredNewUsername = false;
				// If the user already had a BA username, they have the option to keep it or pick a new username.
				if (this.vars.username) {
					var selectedUsername = this.$el
						.find("input[name=username]:checked")
						.val();
					if (!selectedUsername) {
						return {error: "You must select a username."};
					}

					if (selectedUsername === "existing-ba-username") {
						return {username: this.vars.username};
					} else if (selectedUsername === "new-username") {
						enteredNewUsername = true;
					}
				} else {
					// If a user doesn't have any usernames, they have to enter a new one.
					enteredNewUsername = true;
				}

				if (enteredNewUsername) {
					var newUsername = this.$el.find("#new-username-input").val();
					if (!newUsername) {
						return {error: "Please enter a username."};
					} else {
						return {username: newUsername};
					}
				}
				return {error: "Invalid username."};
			}
			return {username: null};
		},
		validateEmail: function () {
			var email = this.$el.find("#email-input").val();
			if (this.vars.emailRequired && !email) {
				return {error: "You must enter an email."};
			}

			if (email) {
				// More sophisticated email validation happens on the backend.
				if (!email.includes("@")) {
					return {error: "Invalid email."};
				}
			}

			return {email};
		},
	});

	Initialize.display = function (options = {}) {
		var popup = new Initialize.Views.Initialize({
			model: Initialize.Models.Master,
		});

		if (options.escapable) {
			popup.$el.showPlainModal({
				height: "auto",
				scrollable: true,
				max_height: "90%",
				max_width: "90%",
			});
		} else {
			AoPS.Ecole.Utils.CreateModalInescapable(popup.$el);
		}
	};

	return Initialize;
})(AoPS.Initialize);
